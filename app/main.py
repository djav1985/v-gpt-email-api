# Importing necessary modules and libraries
import os
import json
import imaplib
import smtplib
import email
from pydantic import BaseModel  # Data validation
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.status import HTTP_403_FORBIDDEN
from email import message_from_bytes, message_from_string, header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header, decode_header
import email.charset as charset
from typing import List, Dict


# Environment variables and basic configurations
BASE_URL = os.getenv("BASE_URL", "http://localhost")
API_KEY = os.getenv("API_KEY")
# Load the ACCOUNTS from environment variable and parse JSON
accounts_json = os.getenv("ACCOUNTS", "[]")  # Default to an empty list if not set
try:
    accounts = json.loads(accounts_json)
except json.JSONDecodeError:
    raise Exception("Failed to decode ACCOUNTS from environment variable")

print("Loaded accounts:", accounts)  # Debugging statement to check the content of parsed accounts

bearer_scheme = HTTPBearer(auto_error=False)  # Avoid auto error to handle no Authorization header gracefully

async def get_api_key(credentials: HTTPAuthorizationCredentials = Security(bearer_scheme)):
    if API_KEY and (not credentials or credentials.credentials != API_KEY):
        raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="Invalid or missing API key")
    return credentials.credentials if credentials else None

# FastAPI application instance
app = FastAPI(
    title="Email Management API",  # API title
    version="0.1.0",  # API version
    description="A FastAPI application that manages email accounts",  # API description
    servers=[{"url": BASE_URL, "description": "Base API server"}]  # Server information
)

class ListFoldersRequest(BaseModel):
    account: str

@app.post("/list_folders")
async def list_folders(request: ListFoldersRequest, api_key: str = Depends(get_api_key)) -> List[str]:
    print(f"Received request for account: {request.account}")  # Debug log

    account_details = next((acc for acc in accounts if acc['email'] == request.account), None)

    if not account_details:
        print("Account details not found.")  # Debug log
        raise HTTPException(status_code=404, detail="Account not found")

    try:
        # Connect to the IMAP server
        mail = imaplib.IMAP4_SSL(account_details['imap_server'])
        # Log in to the server
        mail.login(account_details['email'], account_details['password'])
        # List all folders
        status, folder_list = mail.list()
        if status != 'OK':
            raise HTTPException(status_code=500, detail="Failed to list folders")

        # Extract folder names
        folders = []
        for folder in folder_list:
            flags, delimiter, folder_name = parse_folder_data(folder.decode('utf-8'))
            folders.append(folder_name)

        # Close the connection
        mail.logout()

        return folders
    except imaplib.IMAP4.error as e:
        raise HTTPException(status_code=500, detail=str(e))

def parse_folder_data(folder_data: str):
    parts = folder_data.split(' ')
    flags = parts[0]
    delimiter = parts[1]
    folder_name = ' '.join(parts[2:])
    return flags, delimiter, folder_name.strip('"')

class ListEmailsRequest(BaseModel):
    account: str
    folder: str
    limit: int

@app.post("/list_emails")
async def list_emails(request: ListEmailsRequest, api_key: str = Depends(get_api_key)) -> List[Dict[str, str]]:
    account_details = next((acc for acc in accounts if acc['email'] == request.account), None)
    if not account_details:
        raise HTTPException(status_code=404, detail="Account not found")

    try:
        with imaplib.IMAP4_SSL(account_details['imap_server']) as mail:
            mail.login(account_details['email'], account_details['password'])
            mail.select(request.folder)
            status, data = mail.search(None, 'ALL')
            if status != 'OK':
                raise HTTPException(status_code=500, detail="Failed to search emails")

            email_ids = data[0].split()[-request.limit:]  # Ensuring only recent emails as per limit
            emails = []
            for email_id in email_ids:
                typ, email_data = mail.fetch(email_id, '(RFC822)')
                if typ != 'OK':
                    continue  # Skip if email can't be fetched properly

                email_msg = message_from_bytes(email_data[0][1])
                subject = decode_header_value(email_msg['Subject'])
                from_header = decode_header_value(email_msg['From'])
                date_header = decode_header_value(email_msg['Date'])

                if email_msg.is_multipart():
                    body = ''.join(part.get_payload(decode=True).decode('utf-8') for part in email_msg.get_payload() if part.get_content_type() == 'text/plain')
                else:
                    body = email_msg.get_payload(decode=True).decode('utf-8')

                emails.append({
                    "email_id": email_id.decode('utf-8').strip(),
                    "subject": subject,
                    "from": from_header,
                    "date": date_header,
                    "body_preview": body[:50]
                })

            return emails
    except imaplib.IMAP4.error as e:
        raise HTTPException(status_code=500, detail=str(e))

def decode_header_value(val):
    if val is None:
        return None
    # Set a default charset for unknown encodings
    charset.add_charset('unknown-8bit', charset.SHORTEST, charset.QP, 'utf-8')
    decoded = decode_header(val)
    try:
        return ''.join([str(t[0], t[1] or 'utf-8') if isinstance(t[0], bytes) else t[0] for t in decoded])
    except LookupError:
        # Fallback to utf-8 if the encoding is still unknown
        return ''.join([t[0].decode('utf-8', errors='replace') if isinstance(t[0], bytes) else t[0] for t in decoded])

class ReadEmailsRequest(BaseModel):
    account: str
    folder: str
    email_ids: str  # Expected to be a comma-separated list of email IDs

@app.post("/read_emails")
async def read_emails(request: ReadEmailsRequest, api_key: str = Depends(get_api_key)) -> List[Dict[str, str]]:
    account_details = next((acc for acc in accounts if acc['email'] == request.account), None)
    if not account_details:
        raise HTTPException(status_code=404, detail="Account not found")

    try:
        with imaplib.IMAP4_SSL(account_details['imap_server']) as mail:
            mail.login(account_details['email'], account_details['password'])
            mail.select(request.folder)

            emails = []
            for e_id in request.email_ids.split(','):
                e_id = e_id.strip()
                if not e_id:
                    continue

                status, email_data = mail.fetch(e_id, '(RFC822)')
                if status != 'OK':
                    print(f"Failed to fetch email ID {e_id}: {status}")
                    continue

                raw_email = email_data[0][1].decode('utf-8')
                message = message_from_string(raw_email)  # Use the imported function
                email_details = {
                    "email_id": e_id,
                    "sender": message['From'],
                    "subject": message.get('Subject', "No Subject"),
                    "date": message['Date'],
                    "body": get_email_body(message)
                }
                emails.append(email_details)

            print(emails)  # This will print the emails list to the console
            return emails
    except imaplib.IMAP4.error as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def get_email_body(message):
    try:
        if message.is_multipart():
            for part in message.walk():
                if part.get_content_type() == 'text/plain' and part.get('Content-Disposition') is None:
                    return part.get_payload(decode=True).decode('utf-8')
                elif part.get_content_type() == 'text/html':
                    return part.get_payload(decode=True).decode('utf-8')
        else:
            return message.get_payload(decode=True).decode('utf-8')
    except Exception as e:
        print(f"Error decoding email body: {e}")
        return "Error in decoding email body"

class MoveEmailsRequest(BaseModel):
    account: str
    folder: str
    email_ids: str  # comma-separated list of email IDs
    target_folder: str

@app.post("/move_emails")
async def move_emails(request: MoveEmailsRequest, api_key: str = Depends(get_api_key)) -> Dict[str, str]:
    account_details = next((acc for acc in accounts if acc['email'] == request.account), None)
    if not account_details:
        raise HTTPException(status_code=404, detail="Account not found")

    try:
        mail = imaplib.IMAP4_SSL(account_details['imap_server'])
        mail.login(account_details['email'], account_details['password'])
        mail.select(request.folder)

        email_id_string = ','.join(request.email_ids.split(','))  # Properly split and join email IDs

        status, _ = mail.select(request.target_folder)
        if status == 'NO':
            mail.create(request.target_folder)
            mail.subscribe(request.target_folder)

        # Move emails to the target folder
        result_status, move_data = mail.uid('MOVE', email_id_string, request.target_folder)
        if result_status != 'OK':
            raise HTTPException(status_code=500, detail="Failed to move emails")

        response = {"status": "success", "detail": f"Emails moved to {request.target_folder}"}
        print(response)  # Print the response before returning
        mail.logout()
        return response
    except imaplib.IMAP4.error as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as general_error:
        raise HTTPException(status_code=500, detail=str(general_error))

class SendEmailRequest(BaseModel):
    account: str
    to_address: str
    subject: str
    body: str

@app.post("/send_email")
async def send_email(request: SendEmailRequest, api_key: str = Depends(get_api_key)) -> Dict[str, str]:
    account_details = next((acc for acc in accounts if acc['email'] == request.account), None)
    if not account_details:
        raise HTTPException(status_code=404, detail="Account not found")

    try:
        # Create MIME message
        message = MIMEMultipart()
        message["From"] = account_details['email']
        message["To"] = request.to_address
        message["Subject"] = request.subject
        message.attach(MIMEText(request.body, "plain"))

        # Connect to the SMTP server
        with smtplib.SMTP(account_details['smtp_server'], account_details['smtp_port']) as server:
            server.starttls()  # Can be changed to SMTP_SSL if using SSL from the start
            server.login(account_details['email'], account_details['password'])
            server.sendmail(account_details['email'], request.to_address, message.as_string())

        response = {"status": "success", "detail": f"Email sent successfully to {request.to_address}"}
        print(response)  # Print the response for debugging
        return response
    except smtplib.SMTPException as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as general_error:
        raise HTTPException(status_code=500, detail=str(general_error))

class ReplyEmailRequest(BaseModel):
    account: str
    folder: str
    email_id: str
    reply_body: str

@app.post("/reply_email")
async def reply_email(request: ReplyEmailRequest, api_key: str = Depends(get_api_key)) -> Dict[str, str]:
    # Find the account details from the parsed accounts
    account_details = next((acc for acc in accounts if acc['email'] == request.account), None)
    if not account_details:
        raise HTTPException(status_code=404, detail="Account not found")

    try:
        mail = imaplib.IMAP4_SSL(account_details['imap_server'])
        mail.login(account_details['email'], account_details['password'])
        mail.select(request.folder)  # Correctly reference the folder from request
        result, data = mail.fetch(request.email_id, '(RFC822)')  # Correctly reference the email_id from request
        if result != 'OK':
            raise HTTPException(status_code=500, detail="Failed to fetch the original email")

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

        with smtplib.SMTP(account_details['smtp_server'], account_details['smtp_port']) as server:
            server.starttls()
            server.login(account_details['email'], account_details['password'])
            server.sendmail(account_details['email'], original_sender, reply.as_string())

        mail.logout()

        response = {"status": "success", "detail": f"Reply sent successfully to {original_sender}"}
        print(response)  # Print the response for debugging
        return response
    except imaplib.IMAP4.error as e:
        raise HTTPException(status_code=500, detail=str(e))
    except smtplib.SMTPException as smtp_error:
        raise HTTPException(status_code=500, detail=str(smtp_error))
    except Exception as general_error:
        raise HTTPException(status_code=500, detail=str(general_error))

# Root endpoint serving index.html directly
@app.get("/", include_in_schema=False)
async def root():
    return FileResponse("/app/public/index.html")

# Serve static files (HTML, CSS, JS, images)
app.mount("/static", StaticFiles(directory="/app/public"), name="static")
