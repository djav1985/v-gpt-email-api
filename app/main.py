# Importing standard libraries
import os
import json
import imaplib
import smtplib

# Importing from third-party libraries
from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.responses import FileResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from datetime import datetime
from typing import List, Dict
from email import message_from_bytes
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from starlette.status import HTTP_403_FORBIDDEN

# Importing local modules
from functions import get_account_details, send_email_utility, fetch_email, get_email_body, load_configuration, decode_header_value

# Load configuration on startup
BASE_URL, API_KEY, accounts = load_configuration()

# Setup the bearer token authentication scheme
bearer_scheme = HTTPBearer(auto_error=False)

# Async function to get the API key from the request
async def get_api_key(credentials: HTTPAuthorizationCredentials = Security(bearer_scheme)):
    # If the API key is not provided or does not match the expected value, return a 403 error
    if API_KEY and (not credentials or credentials.credentials != API_KEY):
        raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="Invalid or missing API key")

    # Return the provided API key, or None if it was not provided
    return credentials.credentials if credentials else None

# FastAPI application instance setup
app = FastAPI(
    title="Email Management API",
    version="0.1.0",
    description="A FastAPI application that manages email accounts",
    servers=[{"url": BASE_URL, "description": "Base API server"}]
)

class ListFoldersRequest(BaseModel):
    account: str

class ListEmailsRequest(BaseModel):
    account: str
    folder: str
    limit: int

# Updated ReadEmailsRequest model to accept only one email ID
class ReadEmailsRequest(BaseModel):
    account: str
    folder: str
    email_id: str  # Changed from List[str] to str

class MoveEmailsRequest(BaseModel):
    account: str
    folder: str
    email_id: str
    action: str  # 'trash' or 'spam'

class SendEmailRequest(BaseModel):
    account: str
    to_address: str
    subject: str
    body: str

class ReplyEmailRequest(BaseModel):
    account: str
    folder: str
    email_id: str
    reply_body: str

@app.post("/list_folders", operation_id="list_folders")
async def list_folders(request: ListFoldersRequest, api_key: str = Depends(get_api_key)) -> List[str]:
    account_details = get_account_details(request.account, accounts)

    try:
        with imaplib.IMAP4_SSL(account_details['imap_server']) as mail:
            mail.login(account_details['email'], account_details['password'])
            status, folder_list = mail.list()
            if status != 'OK':
                raise HTTPException(status_code=500, detail="Failed to list folders")

            folders = []
            for folder in folder_list:
                parts = folder.decode('utf-8').split(' ')
                flags = parts[0]
                delimiter = parts[1]
                folder_name = ' '.join(parts[2:]).strip('"')
                folders.append(folder_name)

            return folders
    except imaplib.IMAP4.error as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/list_emails", operation_id="list_emails")
async def list_emails(request: ListEmailsRequest, api_key: str = Depends(get_api_key)) -> List[Dict[str, str]]:
    account_details = get_account_details(request.account, accounts)

    try:
        with imaplib.IMAP4_SSL(account_details['imap_server']) as mail:
            mail.login(account_details['email'], account_details['password'])
            mail.select(request.folder)
            # Retrieve UIDs
            status, data = mail.uid('search', None, 'ALL')
            if status != 'OK':
                raise HTTPException(status_code=500, detail="Failed to search emails")

            # Ensuring only recent emails as per limit
            email_ids = data[0].split()[-request.limit:]
            emails = []
            for email_id in email_ids:
                # Fetch each email by UID
                typ, email_data = mail.uid('fetch', email_id, '(RFC822)')
                if typ != 'OK':
                    continue  # Skip if email can't be fetched properly

                email_msg = message_from_bytes(email_data[0][1])
                subject = decode_header_value(email_msg['Subject'])
                from_header = decode_header_value(email_msg['From'])
                date_header = decode_header_value(email_msg['Date'])

                if email_msg.is_multipart():
                    body = ''.join(part.get_payload(decode=True).decode('utf-8') for part in email_msg.get_payload() if part.get_content_type == 'text/plain')
                else:
                    body = email_msg.get_payload(decode=True).decode('utf-8')

                emails.append({
                    "email_id": email_id.decode('utf-8').strip(),  # Correctly refers to the UID
                    "subject": subject,
                    "from": from_header,
                    "date": date_header,
                    "body_preview": body[:50]  # Showing a preview of the body
                })

            return emails
    except imaplib.IMAP4.error as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/read_emails", operation_id="read_email")
async def read_emails(request: ReadEmailsRequest) -> Dict[str, str]:
    account_details = get_account_details(request.account, accounts)
    data = fetch_email(account_details, request.folder, request.email_id)

    email_msg = message_from_bytes(data[0][1])
    email_body = get_email_body(email_msg)  # Using the imported function

    return {
        "email_id": request.email_id,
        "sender": decode_header_value(email_msg['From']),
        "subject": email_msg.get('Subject', "No Subject"),
        "date": decode_header_value(email_msg['Date']),
        "body": email_body
    }

@app.post("/move_emails", operation_id="move_email")
async def move_emails(request: MoveEmailsRequest, api_key: str = Depends(get_api_key)) -> Dict[str, str]:
    account_details = get_account_details(request.account, accounts)

    try:
        with imaplib.IMAP4_SSL(account_details['imap_server']) as mail:
            mail.login(account_details['email'], account_details['password'])

            # Check server capabilities
            capabilities = mail.capabilities
            if 'MOVE' not in capabilities:
                raise HTTPException(status_code=500, detail="MOVE command not supported by the server")

            mail.select(request.folder)
            target_folder = "Trash" if request.action == "trash" else "Spam"

            # Attempt to move the email
            result_status, move_data = mail.uid('MOVE', request.email_id, target_folder)
            if result_status != 'OK':
                error_detail = move_data[0].decode('utf-8') if move_data and isinstance(move_data[0], bytes) else str(move_data)
                raise HTTPException(status_code=500, detail=f"Failed to move email to {target_folder}: {error_detail}")

            return {"status": "success", "detail": f"Email moved to {target_folder} successfully"}

    except imaplib.IMAP4.error as e:
        raise HTTPException(status_code=500, detail=f"IMAP4 Error: {e}")
    except Exception as general_error:
        raise HTTPException(status_code=500, detail=str(general_error))

@app.post("/send_email", operation_id="send_an_email")
async def send_email(request: SendEmailRequest, api_key: str = Depends(get_api_key)) -> Dict[str, str]:
    account_details = get_account_details(request.account, accounts)

    # Create MIME message
    message = MIMEMultipart()
    message["From"] = account_details['email']
    message["To"] = request.to_address
    message["Subject"] = request.subject
    message.attach(MIMEText(request.body, "plain"))

    send_email_utility(account_details, request.to_address, message)

    response = {"status": "success", "detail": f"Email sent successfully to {request.to_address}"}
    print(response)
    return response

@app.post("/reply_email", operation_id="reply_to_email")
async def reply_email(request: ReplyEmailRequest, api_key: str = Depends(get_api_key)) -> Dict[str, str]:
    account_details = get_account_details(request.account, accounts)
    data = fetch_email(account_details, request.folder, request.email_id)

    original_email = message_from_bytes(data[0][1])
    original_sender = original_email['From']
    original_subject = original_email['Subject']
    in_reply_to = original_email.get('Message-ID', '')

    reply = MIMEMultipart()
    reply['From'] = account_details['email']
    reply['To'] = original_sender
    reply['Subject'] = 'RE: ' + original_subject
    reply['In-Reply-To'] = in_reply_to
    reply['References'] = in_reply_to
    reply.attach(MIMEText(request.reply_body, 'plain'))

    send_email_utility(account_details, original_sender, reply)

    response = {"status": "success", "detail": f"Reply sent successfully to {original_sender}"}
    print(response)
    return response

# Root endpoint serving index.html directly
@app.get("/", include_in_schema=False)
async def root():
    return FileResponse("/app/public/index.html")

# Serve static files (HTML, CSS, JS, images)
app.mount("/static", StaticFiles(directory="/app/public"), name="static")
