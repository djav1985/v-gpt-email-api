from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from app.models import SendEmailRequest
from app.dependencies import send_email, get_api_key

send_router = APIRouter()

@send_router.post("/", operation_id="send_email")
async def send_email_endpoint(
    request: SendEmailRequest, _api_key: Optional[str] = Depends(get_api_key)
):
    """Send an email using the data provided in ``request``.

    Args:
        request: Payload containing recipients, subject, body and optional file URLs.
        _api_key: Optional API key validated via dependency injection.

    Returns:
        A success message upon completion.

    Raises:
        HTTPException: If sending the email fails.
    """
    to_addresses = request.to_address
    subject = request.subject
    body = request.body
    file_url = request.file_url

    try:
        await send_email(to_addresses, subject, body, file_url)
        return {"message": "Email sent successfully"}
    except HTTPException as e:
        print(f"HTTPException: {e.detail}")
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
