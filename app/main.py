# Importing necessary modules and libraries
import os
import json
import imaplib
import smtplib
from pydantic import BaseModel  # Data validation
from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.status import HTTP_403_FORBIDDEN
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
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
        mail = imaplib.IMAP4_SSL(account_details['imap_server'])
        mail.login(account_details['email'], account_details['password'])
        mail.select(request.folder)
        status, data = mail.search(None, 'ALL')
        if status != 'OK':
            raise HTTPException(status_code=500, detail="Failed to search emails")

        email_ids = data[0].split()[-request.limit:]  # Properly using request.limit
        emails = []
        for email_data_bytes in email_ids:
            email_data_str = email_data_bytes.decode('utf-8')
            # Parsing the email data structure
            parts = email_data_str.split('" "')
            email_id = parts[7].strip("<>")  # Extracting email ID from the last part
            sender = parts[6]  # Extracting sender from the second last part
            subject = parts[1]  # Extracting subject from the second part
            # Creating email details dictionary
            email_details = {
                "email_id": email_id,
                "sender": sender,
                "subject": subject if subject else "No Subject"
            }
            emails.append(email_details)

        mail.logout()
        return emails
    except imaplib.IMAP4.error as e:
        raise HTTPException(status_code=500, detail=str(e))



class ReadEmailsRequest(BaseModel):
    account: str
    folder: str
    email_ids: str  # Expected to be a comma-separated list of email IDs

@app.post("/read_emails")
async def read_emails(request: ReadEmailsRequest, api_key: str = Depends(get_api_key)) -> List[Dict[str, str]]:
    # Find the account details from the parsed accounts
    account_details = next((acc for acc in accounts if acc['email'] == request.account), None)

    if not account_details:
        raise HTTPException(status_code=404, detail="Account not found")

    try:
        # Connect to the IMAP server
        mail = imaplib.IMAP4_SSL(account_details['imap_server'])
        # Log in to the server
        mail.login(account_details['email'], account_details['password'])
        # Select the folder
        mail.select(folder)

        # Fetch each email by ID
        emails = []
        for e_id in email_ids.split(','):
            # Fetch specific email's envelope and body
            status, email_data = mail.fetch(e_id, '(RFC822)')
            if status != 'OK':
                continue  # Skip if unable to fetch the email

            # Parse email data
            raw_email = email_data[0][1].decode('utf-8')
            message = email.message_from_string(raw_email)
            email_details = {
                "email_id": e_id,
                "sender": message['From'],
                "subject": message.get('Subject', "No Subject"),
                "body": get_email_body(message)
            }
            emails.append(email_details)

        # Logout from the mail server
        mail.logout()

        return emails
    except imaplib.IMAP4.error as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def get_email_body(message):
    """Utility function to extract the body from an email message object."""
    if message.is_multipart():
        for part in message.walk():
            ctype = part.get_content_type()
            cdispo = str(part.get('Content-Disposition'))

            # skip any text/plain (txt) attachments
            if ctype == 'text/plain' and 'attachment' not in cdispo:
                return part.get_payload(decode=True).decode('utf-8')  # decode
            elif ctype == 'text/html':
                return part.get_payload(decode=True).decode('utf-8')  # to convert byte code to string
    else:
        return message.get_payload(decode=True).decode('utf-8')

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

        result_status, move_data = mail.uid('MOVE', email_id_string, request.target_folder)
        if result_status != 'OK':
            raise HTTPException(status_code=500, detail="Failed to move emails")

        mail.logout()
        return {"status": "success", "detail": f"Emails moved to {request.target_folder}"}
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
    # Find the account details from the parsed accounts
    account_details = next((acc for acc in accounts if acc['email'] == request.account), None)

    if not account_details:
        raise HTTPException(status_code=404, detail="Account not found")

    try:
        # Create MIME message
        message = MIMEMultipart()
        message["From"] = account_details['email']
        message["To"] = to_address
        message["Subject"] = subject
        message.attach(MIMEText(body, "plain"))

        # Connect to the SMTP server
        with smtplib.SMTP(account_details['smtp_server'], account_details['smtp_port']) as server:
            server.starttls()  # Can be changed to SMTP_SSL if using SSL from the start
            server.login(account_details['email'], account_details['password'])
            server.sendmail(account_details['email'], to_address, message.as_string())

        return {"status": "success", "detail": "Email sent successfully to {}".format(to_address)}
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
        # Connect to the IMAP server to fetch the original email
        mail = imaplib.IMAP4_SSL(account_details['imap_server'])
        mail.login(account_details['email'], account_details['password'])
        mail.select(folder)
        result, data = mail.fetch(email_id, '(RFC822)')
        if result != 'OK':
            raise HTTPException(status_code=500, detail="Failed to fetch the original email")

        # Parse the original email
        original_email = email.message_from_bytes(data[0][1])
        original_sender = original_email['From']
        original_subject = original_email['Subject']
        in_reply_to = original_email.get('Message-ID', '')

        # Create the reply email
        reply = MIMEMultipart()
        reply['From'] = account_details['email']
        reply['To'] = original_sender
        reply['Subject'] = 'RE: ' + original_subject
        reply['In-Reply-To'] = in_reply_to
        reply['References'] = in_reply_to
        reply.attach(MIMEText(reply_body, 'plain'))

        # Connect to the SMTP server to send the reply
        with smtplib.SMTP(account_details['smtp_server'], account_details['smtp_port']) as server:
            server.starttls()
            server.login(account_details['email'], account_details['password'])
            server.sendmail(account_details['email'], original_sender, reply.as_string())

        mail.logout()

        return {"status": "success", "detail": "Reply sent successfully to {}".format(original_sender)}
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
