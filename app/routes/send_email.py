import logging
from fastapi import APIRouter, Body, HTTPException, Security
from ..models import SendEmailRequest, MessageResponse, ErrorResponse
from ..dependencies import send_email, get_api_key

send_router = APIRouter(tags=["Send"])
logger = logging.getLogger(__name__)


@send_router.post(
    "/",
    operation_id="send_email",
    dependencies=[Security(get_api_key)],
    summary="Send an email",
    description="Send an email to one or more recipients.",
    status_code=200,
    response_model=MessageResponse,
    responses={
        200: {
            "content": {
                "application/json": {
                    "example": {"message": "Email sent successfully"}
                }
            }
        },
        400: {
            "model": ErrorResponse,
            "description": "Invalid request",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Invalid request",
                        "code": "invalid_request",
                    }
                }
            },
        },
        401: {
            "model": ErrorResponse,
            "description": "Missing API key",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Not authenticated",
                        "code": "not_authenticated",
                    }
                }
            },
        },
        403: {
            "model": ErrorResponse,
            "description": "Forbidden",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Not authorized",
                        "code": "not_authorized",
                    }
                }
            },
        },
        500: {
            "model": ErrorResponse,
            "description": "Server error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Server error",
                        "code": "server_error",
                    }
                }
            },
        },
    },
)
async def send_email_endpoint(
    request: SendEmailRequest = Body(
        ...,
        examples={
            "basic": {
                "summary": "Simple email",
                "value": {
                    "to_addresses": ["recipient@example.com"],
                    "subject": "Greetings",
                    "body": "Hello there!",
                },
            }
        },
    )
) -> MessageResponse:
    subject = request.subject
    body = request.body
    file_urls = (
        [str(url) for url in request.file_url] if request.file_url else None
    )

    try:
        await send_email(
            request.to_addresses, subject, body, file_urls=file_urls
        )
        return MessageResponse(message="Email sent successfully")
    except HTTPException as e:
        logger.error("HTTPException: %s", e.detail)
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception as e:
        logger.exception("Unexpected error while sending email")
        raise HTTPException(status_code=500, detail=str(e))
