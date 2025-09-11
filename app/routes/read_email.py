# flake8: noqa
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from fastapi import APIRouter, Body, HTTPException, Path, Query, Security

from ..dependencies import get_api_key, send_email
from ..models import EmailSummary, ErrorResponse, MessageResponse, SendEmailRequest
from ..services import imap_client
from .. import dependencies

read_router = APIRouter(tags=["Read"])


@read_router.get(
    "/emails",
    response_model=list[EmailSummary],
    dependencies=[Security(get_api_key)],
    summary="Fetch emails",
    description="Return emails from the specified folder.",
    operation_id="fetch_emails",
    responses={
        200: {
            "content": {
                "application/json": {
                    "example": [
                        {
                            "uid": "1",
                            "subject": "Hello",
                            "from": "sender@example.com",
                            "date": "2024-01-01T12:00:00Z",
                            "seen": False,
                        }
                    ]
                }
            }
        },
        400: {
            "model": ErrorResponse,
            "description": "Invalid request",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid request", "code": "invalid_request"}
                }
            },
        },
        401: {
            "model": ErrorResponse,
            "description": "Missing API key",
            "content": {
                "application/json": {
                    "example": {"detail": "Not authenticated", "code": "not_authenticated"}
                }
            },
        },
        403: {
            "model": ErrorResponse,
            "description": "Forbidden",
            "content": {
                "application/json": {
                    "example": {"detail": "Not authorized", "code": "not_authorized"}
                }
            },
        },
        404: {
            "model": ErrorResponse,
            "description": "Emails not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Emails not found", "code": "not_found"}
                }
            },
        },
        500: {
            "model": ErrorResponse,
            "description": "Server error",
            "content": {
                "application/json": {
                    "example": {"detail": "Server error", "code": "server_error"}
                }
            },
        },
    },
)
async def get_emails(
    limit: int = Query(10, description="Maximum number of emails to return"),
    unread: bool = Query(False, description="Only fetch unread emails"),
    folder: str = Query("INBOX", description="Mail folder to read from"),
) -> list[EmailSummary]:
    try:
        return await imap_client.fetch_messages(folder, limit, unread)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@read_router.get(
    "/folders",
    dependencies=[Security(get_api_key)],
    summary="List mail folders",
    description="List available mail folders.",
    operation_id="list_folders",
    responses={
        200: {
            "content": {
                "application/json": {"example": ["INBOX", "Archive"]}
            }
        },
        400: {
            "model": ErrorResponse,
            "description": "Invalid request",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid request", "code": "invalid_request"}
                }
            },
        },
        401: {
            "model": ErrorResponse,
            "description": "Missing API key",
            "content": {
                "application/json": {
                    "example": {"detail": "Not authenticated", "code": "not_authenticated"}
                }
            },
        },
        403: {
            "model": ErrorResponse,
            "description": "Forbidden",
            "content": {
                "application/json": {
                    "example": {"detail": "Not authorized", "code": "not_authorized"}
                }
            },
        },
        404: {
            "model": ErrorResponse,
            "description": "Folders not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Folders not found", "code": "not_found"}
                }
            },
        },
        500: {
            "model": ErrorResponse,
            "description": "Server error",
            "content": {
                "application/json": {
                    "example": {"detail": "Server error", "code": "server_error"}
                }
            },
        },
    },
)
async def get_folders() -> list[str]:
    try:
        return await imap_client.list_mailboxes()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@read_router.post(
    "/emails/{uid}/move",
    dependencies=[Security(get_api_key)],
    summary="Move an email",
    description="Move an email to another folder.",
    response_model=MessageResponse,
    operation_id="move_email",
    responses={
        200: {
            "content": {
                "application/json": {
                    "example": {"message": "Email moved"}
                }
            }
        },
        400: {
            "model": ErrorResponse,
            "description": "Invalid request",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid request", "code": "invalid_request"}
                }
            },
        },
        401: {
            "model": ErrorResponse,
            "description": "Missing API key",
            "content": {
                "application/json": {
                    "example": {"detail": "Not authenticated", "code": "not_authenticated"}
                }
            },
        },
        403: {
            "model": ErrorResponse,
            "description": "Forbidden",
            "content": {
                "application/json": {
                    "example": {"detail": "Not authorized", "code": "not_authorized"}
                }
            },
        },
        404: {
            "model": ErrorResponse,
            "description": "Email not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Email not found", "code": "not_found"}
                }
            },
        },
        500: {
            "model": ErrorResponse,
            "description": "Server error",
            "content": {
                "application/json": {
                    "example": {"detail": "Server error", "code": "server_error"}
                }
            },
        },
    },
)
async def move_email(
    uid: str = Path(..., description="UID of the email to move"),
    folder: str = Query(..., description="Destination folder"),
    source_folder: str = Query("INBOX", description="Source folder"),
) -> MessageResponse:
    try:
        await imap_client.move_message(uid, folder, source_folder)
        return MessageResponse(message="Email moved")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@read_router.post(
    "/emails/{uid}/forward",
    dependencies=[Security(get_api_key)],
    summary="Forward an email",
    description="Forward an existing email to new recipients.",
    response_model=MessageResponse,
    operation_id="forward_email",
    responses={
        200: {
            "content": {
                "application/json": {
                    "example": {"message": "Email forwarded"}
                }
            }
        },
        400: {
            "model": ErrorResponse,
            "description": "Invalid request",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid request", "code": "invalid_request"}
                }
            },
        },
        401: {
            "model": ErrorResponse,
            "description": "Missing API key",
            "content": {
                "application/json": {
                    "example": {"detail": "Not authenticated", "code": "not_authenticated"}
                }
            },
        },
        403: {
            "model": ErrorResponse,
            "description": "Forbidden",
            "content": {
                "application/json": {
                    "example": {"detail": "Not authorized", "code": "not_authorized"}
                }
            },
        },
        404: {
            "model": ErrorResponse,
            "description": "Email not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Email not found", "code": "not_found"}
                }
            },
        },
        500: {
            "model": ErrorResponse,
            "description": "Server error",
            "content": {
                "application/json": {
                    "example": {"detail": "Server error", "code": "server_error"}
                }
            },
        },
    },
)
async def forward_email(
    uid: str = Path(..., description="UID of the email to forward"),
    request: SendEmailRequest = Body(
        ...,
        examples={
            "basic": {
                "summary": "Forward email",
                "value": {
                    "to_addresses": ["recipient@example.com"],
                    "subject": "Fwd: Greetings",
                    "body": "See attached",
                },
            }
        },
    ),
) -> MessageResponse:
    try:
        original = await imap_client.fetch_message(uid)
        body = imap_client.extract_body(original)
        subject = request.subject or imap_client.decode_header_value(original.get("Subject", ""))
        msg_id = original.get("Message-ID")
        headers = {}
        if msg_id:
            headers["In-Reply-To"] = msg_id
            headers["References"] = msg_id
        file_urls = [str(url) for url in request.file_url] if request.file_url else None
        await send_email(
            request.to_addresses, subject, body, file_urls=file_urls, headers=headers
        )
        return MessageResponse(message="Email forwarded")
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@read_router.post(
    "/emails/{uid}/reply",
    dependencies=[Security(get_api_key)],
    summary="Reply to an email",
    description="Reply to an existing email.",
    response_model=MessageResponse,
    operation_id="reply_email",
    responses={
        200: {
            "content": {
                "application/json": {
                    "example": {"message": "Email sent"}
                }
            }
        },
        400: {
            "model": ErrorResponse,
            "description": "Invalid request",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid request", "code": "invalid_request"}
                }
            },
        },
        401: {
            "model": ErrorResponse,
            "description": "Missing API key",
            "content": {
                "application/json": {
                    "example": {"detail": "Not authenticated", "code": "not_authenticated"}
                }
            },
        },
        403: {
            "model": ErrorResponse,
            "description": "Forbidden",
            "content": {
                "application/json": {
                    "example": {"detail": "Not authorized", "code": "not_authorized"}
                }
            },
        },
        404: {
            "model": ErrorResponse,
            "description": "Email not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Email not found", "code": "not_found"}
                }
            },
        },
        500: {
            "model": ErrorResponse,
            "description": "Server error",
            "content": {
                "application/json": {
                    "example": {"detail": "Server error", "code": "server_error"}
                }
            },
        },
    },
)
async def reply_email(
    uid: str = Path(..., description="UID of the email to reply to"),
    request: SendEmailRequest = Body(
        ...,
        examples={
            "basic": {
                "summary": "Reply to email",
                "value": {
                    "to_addresses": ["recipient@example.com"],
                    "subject": "Re: Greetings",
                    "body": "Thanks!",
                },
            }
        },
    ),
) -> MessageResponse:
    try:
        original = await imap_client.fetch_message(uid)
        body = request.body or imap_client.extract_body(original)
        subj = imap_client.decode_header_value(original.get("Subject", ""))
        subject = request.subject or f"Re: {subj}"
        msg_id = original.get("Message-ID")
        headers = {}
        if msg_id:
            headers["In-Reply-To"] = msg_id
            headers["References"] = msg_id
        file_urls = [str(url) for url in request.file_url] if request.file_url else None
        await send_email(
            request.to_addresses, subject, body, file_urls=file_urls, headers=headers
        )
        return MessageResponse(message="Email sent")
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@read_router.delete(
    "/emails/{uid}",
    dependencies=[Security(get_api_key)],
    summary="Delete an email",
    description="Delete an email from a folder.",
    response_model=MessageResponse,
    operation_id="delete_email",
    responses={
        200: {
            "content": {
                "application/json": {
                    "example": {"message": "Email deleted"}
                }
            }
        },
        400: {
            "model": ErrorResponse,
            "description": "Invalid request",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid request", "code": "invalid_request"}
                }
            },
        },
        401: {
            "model": ErrorResponse,
            "description": "Missing API key",
            "content": {
                "application/json": {
                    "example": {"detail": "Not authenticated", "code": "not_authenticated"}
                }
            },
        },
        403: {
            "model": ErrorResponse,
            "description": "Forbidden",
            "content": {
                "application/json": {
                    "example": {"detail": "Not authorized", "code": "not_authorized"}
                }
            },
        },
        404: {
            "model": ErrorResponse,
            "description": "Email not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Email not found", "code": "not_found"}
                }
            },
        },
        500: {
            "model": ErrorResponse,
            "description": "Server error",
            "content": {
                "application/json": {
                    "example": {"detail": "Server error", "code": "server_error"}
                }
            },
        },
    },
)
async def delete_email(
    uid: str = Path(..., description="UID of the email to delete"),
    folder: str = Query("INBOX", description="Folder containing the email"),
) -> MessageResponse:
    try:
        await imap_client.delete_message(uid, folder)
        return MessageResponse(message="Email deleted")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@read_router.post(
    "/drafts",
    dependencies=[Security(get_api_key)],
    summary="Create a draft email",
    description="Store an email draft in the Drafts folder.",
    response_model=MessageResponse,
    operation_id="create_draft",
    responses={
        200: {
            "content": {
                "application/json": {
                    "example": {"message": "Draft stored"}
                }
            }
        },
        400: {
            "model": ErrorResponse,
            "description": "Invalid request",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid request", "code": "invalid_request"}
                }
            },
        },
        401: {
            "model": ErrorResponse,
            "description": "Missing API key",
            "content": {
                "application/json": {
                    "example": {"detail": "Not authenticated", "code": "not_authenticated"}
                }
            },
        },
        403: {
            "model": ErrorResponse,
            "description": "Forbidden",
            "content": {
                "application/json": {
                    "example": {"detail": "Not authorized", "code": "not_authorized"}
                }
            },
        },
        404: {
            "model": ErrorResponse,
            "description": "Folder not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Folder not found", "code": "not_found"}
                }
            },
        },
        500: {
            "model": ErrorResponse,
            "description": "Server error",
            "content": {
                "application/json": {
                    "example": {"detail": "Server error", "code": "server_error"}
                }
            },
        },
    },
)
async def create_draft(
    request: SendEmailRequest = Body(
        ...,
        examples={
            "basic": {
                "summary": "Draft email",
                "value": {
                    "to_addresses": ["recipient@example.com"],
                    "subject": "Draft",
                    "body": "Draft body",
                },
            }
        },
    )
) -> MessageResponse:
    if dependencies.settings is None:
        raise HTTPException(status_code=500, detail="Settings have not been initialized")
    msg = MIMEMultipart()
    msg["From"] = dependencies.settings.account_email
    msg["To"] = ", ".join(request.to_addresses)
    msg["Subject"] = request.subject
    msg.attach(MIMEText(request.body, "html"))
    try:
        await imap_client.append_message("Drafts", msg)
        return MessageResponse(message="Draft stored")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
