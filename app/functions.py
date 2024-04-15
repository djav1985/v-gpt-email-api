import os
import json
import smtplib
import imaplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from fastapi import HTTPException
from email import message_from_bytes
from email.header import decode_header
import re

def get_account_details(email: str, accounts):
    account_details = next((acc for acc in accounts if acc['email'] == email), None)
    if not account_details:
        raise HTTPException(status_code=404, detail="Account not found")
    return account_details

def send_email_utility(account_details, to_address, email_message):
    try:
        # Connect to the SMTP server
        with smtplib.SMTP(account_details['smtp_server'], account_details['smtp_port']) as server:
            server.starttls()  # Can be changed to SMTP_SSL if using SSL from the start
            server.login(account_details['email'], account_details['password'])
            server.sendmail(account_details['email'], to_address, email_message.as_string())
    except smtplib.SMTPException as e:
        raise HTTPException(status_code=500, detail=str(e))

def fetch_email(account_details, folder, email_id):
    mail = imaplib.IMAP4_SSL(account_details['imap_server'])
    try:
        mail.login(account_details['email'], account_details['password'])
        mail.select(folder)  # Access the specified folder
        # Fetch the specified email using UID
        result, data = mail.uid('fetch', email_id, '(RFC822)')
        if result != 'OK':
            raise HTTPException(status_code=500, detail="Failed to fetch the original email")
        return data
    finally:
        mail.logout()

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

def decode_header_value(val):
    if val is None:
        return None

    # Decode the header using email's decode_header function
    decoded_parts = decode_header(val)

    # Process each part of the decoded header
    decoded_string = ""
    for part, encoding in decoded_parts:
        if isinstance(part, bytes):
            # Forcefully decode bytes to string using utf-8, ignoring errors
            part = part.decode('utf-8', errors='ignore')

        # Sanitize the string by removing surrogates and other non-UTF-8 characters
        part = re.sub(r'[\ud800-\udfff]', '', part)

        # Append the sanitized part to the decoded string
        decoded_string += part

    # Return the sanitized and decoded string
    return decoded_string

# Load configuration from environment variables
def load_configuration():
    # The base URL for the application, defaulting to "http://localhost"
    BASE_URL = os.getenv("BASE_URL", "http://localhost")

    # The API key for authentication
    API_KEY = os.getenv("API_KEY")

    # A JSON string of account details
    accounts_json = os.getenv("ACCOUNTS", "[]")
    try:
        # Parse the accounts JSON string into a Python list
        accounts = json.loads(accounts_json)
    except json.JSONDecodeError:
        raise Exception("Failed to decode ACCOUNTS from environment variable")

    print("Loaded accounts:", accounts)
    return BASE_URL, API_KEY, accounts
