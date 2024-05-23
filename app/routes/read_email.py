from fastapi import APIRouter, HTTPException
from email import message_from_bytes
from typing import Dict
from models import ReadEmailsRequest
from dependencies import (
    get_account_details,
    fetch_email,
    get_email_body,
    decode_header_value,
)

read_router = APIRouter()


@read_router.post("/read_emails", operation_id="read_email")
async def read_emails(request: ReadEmailsRequest) -> Dict[str, str]:
    try:
        account_details = await get_account_details(request.account)
    except HTTPException as e:
        print(f"Error fetching account details: {e.detail}")
        raise HTTPException(status_code=404, detail="Account not found")

    try:
        data = await fetch_email(account_details, request.folder, request.email_id)
        email_msg = message_from_bytes(data)
        email_body = await get_email_body(email_msg)

        response = {
            "email_id": request.email_id,
            "sender": await decode_header_value(email_msg["From"]),
            "subject": email_msg.get("Subject", "No Subject"),
            "date": await decode_header_value(email_msg["Date"]),
            "body": email_body,
        }
        print(f"Read email response: {response}")
        return response
    except Exception as e:
        print(f"Error reading email: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error reading email: {str(e)}")
