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
    decode_header_value,
)

# Creating an instance of the FastAPI router
send_router = APIRouter()


@send_router.post("/send_email", operation_id="send_an_email")
async def send_email(request: SendEmailRequest, api_key: str = Depends(get_api_key)):
    try:
        account_details = await get_account_details(request.account)
    except HTTPException as e:
        raise HTTPException(status_code=404, detail="Account not found")

    if request.email_id:
        # Reply to an existing email
        try:
            data = await fetch_email(account_details, request.folder, request.email_id)
            original_email = message_from_bytes(data[0][1])
            original_sender = original_email["From"]
            original_subject = original_email["Subject"]
            in_reply_to = original_email.get("Message-ID", "")

            message = MIMEMultipart()
            message["From"] = account_details["email"]
            message["To"] = original_sender
            message["Subject"] = "RE: " + original_subject
            message["In-Reply-To"] = in_reply_to
            message["References"] = in_reply_to
            message.attach(MIMEText(request.body, "plain"))

            await send_email_utility(account_details, original_sender, message)

            response = {
                "status": "success",
                "detail": f"Reply sent successfully to {original_sender}",
            }
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Error sending reply: {str(e)}"
            )
    else:
        # Send a new email
        try:
            message = MIMEMultipart()
            message["From"] = account_details["email"]
            message["To"] = request.to_address
            message["Subject"] = request.subject
            message.attach(MIMEText(request.body, "plain"))

            await send_email_utility(account_details, request.to_address, message)

            response = {
                "status": "success",
                "detail": f"Email sent successfully to {request.to_address}",
            }
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Error sending email: {str(e)}"
            )

    print(response)
    return response
