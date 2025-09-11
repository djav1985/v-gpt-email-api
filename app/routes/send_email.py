from fastapi import APIRouter, Depends, HTTPException
from ..models import SendEmailRequest, MessageResponse
from ..dependencies import send_email, get_api_key

send_router = APIRouter(tags=["Send"])


@send_router.post(
    "/",
    operation_id="send_email",
    dependencies=[Depends(get_api_key)],
    summary="Send an email",
    description="Send an email to one or more recipients.",
    status_code=201,
    response_model=MessageResponse,
    responses={
        400: {"description": "Invalid request"},
        500: {"description": "Server error"},
    },
)
async def send_email_endpoint(request: SendEmailRequest) -> MessageResponse:
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
        print(f"HTTPException: {e.detail}")
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
