"""Route for sending emails."""

import logging

from fastapi import APIRouter, Body, HTTPException, Security

from ..dependencies import get_api_key, send_email
from ..models import MessageResponse, SendEmailRequest
from . import COMMON_ERROR_RESPONSES

send_router = APIRouter(tags=["Send"])
logger = logging.getLogger(__name__)


@send_router.post(
    "/",
    operation_id="send_email",
    dependencies=[Security(get_api_key)],
    summary="Send an email",
    description="Send an email to one or more recipients.",
    status_code=201,
    response_model=MessageResponse,
    responses={
        201: {
            "content": {
                "application/json": {"example": {"message": "Email sent successfully"}}
            }
        },
        **COMMON_ERROR_RESPONSES,
    },
)
async def send_email_endpoint(
    request: SendEmailRequest = Body(
            ...,
            examples=[
                {
                    "summary": "Simple email",
                    "value": {
                        "to_addresses": ["recipient@example.com"],
                        "subject": "Greetings",
                        "body": "Hello there!",
                    },
                }
            ],
    )
) -> MessageResponse:
    """Handle POST requests for sending an email."""
    subject = request.subject
    body = request.body
    file_urls = [str(url) for url in request.file_urls] if request.file_urls else None

    try:
        await send_email(request.to_addresses, subject, body, file_urls=file_urls)
        return MessageResponse(message="Email sent successfully")
    except HTTPException as e:
        logger.error("HTTPException: %s", e.detail)
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception as e:
        logger.exception("Unexpected error while sending email")
        raise HTTPException(status_code=500, detail=str(e))
