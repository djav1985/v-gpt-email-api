from fastapi import APIRouter, Depends, HTTPException
from email import message_from_bytes
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from models import SendEmailRequest
from dependencies import (
    get_api_key,
    get_account_details,
    fetch_email,
    send_email_utility,
)

# Create an instance of the FastAPI router
send_router = APIRouter()


@send_router.post("/send_email", operation_id="send_an_email")
async def send_email(request: SendEmailRequest, api_key: str = Depends(get_api_key)):
    try:
        account_details = await get_account_details(request.account)
        print(f"Account details fetched: {account_details}")
    except HTTPException as e:
        print(f"Error fetching account details: {e.detail}")
        raise HTTPException(status_code=404, detail="Account not found")

    message = MIMEMultipart()
    message["From"] = account_details["email"]

    try:
        if request.email_id:
            # Reply to an existing email
            data = await fetch_email(account_details, request.folder, request.email_id)
            original_email = message_from_bytes(data[0][1])
            original_sender = original_email["From"]
            original_subject = original_email["Subject"]
            in_reply_to = original_email.get("Message-ID", "")
            message["To"] = original_sender
            message["Subject"] = f"RE: {original_subject}"
            message["In-Reply-To"] = in_reply_to
            message["References"] = in_reply_to
            response_detail = f"Reply sent successfully to {original_sender}"
            print(f"Preparing to reply to email from: {original_sender}")
        else:
            # Send a new email
            message["To"] = request.to_address
            message["Subject"] = request.subject
            response_detail = f"Email sent successfully to {request.to_address}"
            print(f"Preparing to send new email to: {request.to_address}")

        message.attach(MIMEText(request.body, "plain"))
        recipient = message["To"]
        await send_email_utility(account_details, recipient, message)

        response = {
            "status": "success",
            "detail": response_detail,
        }
        print(f"Email sent successfully. Response: {response}")
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error sending email: {str(e)}")
    return response
