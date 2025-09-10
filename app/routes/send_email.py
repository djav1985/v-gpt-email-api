from fastapi import APIRouter, Depends, HTTPException
from ..models import SendEmailRequest
from ..dependencies import send_email, get_api_key

send_router = APIRouter()


@send_router.post("/", operation_id="send_email", dependencies=[Depends(get_api_key)])
async def send_email_endpoint(request: SendEmailRequest):
    subject = request.subject
    body = request.body
    file_url = request.file_url

    try:
        await send_email(request.to_addresses, subject, body, file_url)
        return {"message": "Email sent successfully"}
    except HTTPException as e:
        print(f"HTTPException: {e.detail}")
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
