import os
import json
import re

import aiosmtplib
from aioimaplib import aioimaplib, IMAP4_SSL

from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from email import message_from_bytes, policy
from email.header import decode_header


def validate_account_sync(email: str):
    accounts = json.loads(os.getenv("ACCOUNTS", "[]"))
    account_details = next((acc for acc in accounts if acc["email"] == email), None)
    if not account_details:
        raise ValueError("Account not found")
    return account_details


async def get_account_details(email: str):
    accounts = json.loads(os.getenv("ACCOUNTS", "[]"))
    account_details = next((acc for acc in accounts if acc["email"] == email), None)
    if not account_details:
        raise HTTPException(status_code=404, detail="Account not found")
    return account_details


async def send_email_utility(account_details, to_address, email_message):
    try:
        async with aiosmtplib.SMTP(
            hostname=account_details["smtp_server"], port=account_details["smtp_port"]
        ) as server:
            await server.starttls()
            await server.login(account_details["email"], account_details["password"])
            await server.sendmail(
                account_details["email"], to_address, email_message.as_string()
            )
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error sending email: {str(e)}")


async def fetch_email(account_details, folder, email_id):
    mail = aioimaplib.IMAP4_SSL(account_details["imap_server"])
    try:
        await mail.wait_hello_from_server()
        await mail.login(account_details["email"], account_details["password"])
        await mail.select(folder)
        result, data = await mail.uid("fetch", email_id, "(RFC822)")
        if result != "OK":
            raise HTTPException(status_code=500, detail="Failed to fetch the email")
        return data[0][1]  # assuming data[0][1] contains the email content
    except Exception as e:
        print(f"Error fetching email: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching email: {str(e)}")
    finally:
        await mail.logout()


async def get_email_body(message):
    try:
        if message.is_multipart():
            for part in message.walk():
                if (
                    part.get_content_type() == "text/plain"
                    and part.get("Content-Disposition") is None
                ):
                    return part.get_payload(decode=True).decode(
                        "utf-8", errors="ignore"
                    )
                elif (
                    part.get_content_type() == "text/html"
                    and part.get("Content-Disposition") is None
                ):
                    return part.get_payload(decode=True).decode(
                        "utf-8", errors="ignore"
                    )
        else:
            return message.get_payload(decode=True).decode("utf-8", errors="ignore")
    except Exception as e:
        print(f"Error decoding email body: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error decoding email body: {str(e)}"
        )


async def decode_header_value(val):
    try:
        if val is None:
            return None

        decoded_parts = decode_header(val)
        decoded_string = ""
        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                part = part.decode(encoding if encoding else "utf-8", errors="ignore")
            part = re.sub(r"[\ud800-\udfff]", "", part)
            decoded_string += part
        return decoded_string
    except Exception as e:
        print(f"Error decoding header value: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error decoding header value: {str(e)}"
        )


async def get_api_key(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False)),
):
    try:
        api_key = os.getenv("API_KEY")
        if api_key and (not credentials or credentials.credentials != api_key):
            raise HTTPException(status_code=403, detail="Invalid or missing API key")
        return credentials.credentials if credentials else None
    except Exception as e:
        print(f"Error retrieving API key: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error retrieving API key: {str(e)}"
        )
