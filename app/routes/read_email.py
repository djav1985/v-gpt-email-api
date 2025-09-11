"""Routes for reading, manipulating, and drafting emails."""

from fastapi import APIRouter, Body, HTTPException, Path, Query, Security

from ..dependencies import get_api_key, send_email
from ..models import (
    EmailSummary,
    ErrorResponse,
    FoldersResponse,
    MessageResponse,
    SendEmailRequest,
)
from . import COMMON_ERROR_RESPONSES, imap
from .imap import create_draft_action, delete_email_action, move_email_action

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
        404: {
            "model": ErrorResponse,
            "description": "Emails not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Emails not found", "code": "not_found"}
                }
            },
        },
        **COMMON_ERROR_RESPONSES,
    },
)
async def get_emails(
    limit: int = Query(10, gt=0, description="Maximum number of emails to return"),
    unread: bool = Query(False, description="Only fetch unread emails"),
    folder: str = Query("INBOX", description="Mail folder to read from"),
) -> list[EmailSummary]:
    """Retrieve email summaries from the specified folder."""
    try:
        return await imap.fetch_messages(folder, limit, unread)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@read_router.get(
    "/folders",
    dependencies=[Security(get_api_key)],
    response_model=FoldersResponse,
    summary="List mail folders",
    description="List available mail folders.",
    operation_id="list_folders",
    responses={
        200: {
            "content": {"application/json": {"example": {"folders": ["INBOX", "Archive"]}}}
        },
        404: {
            "model": ErrorResponse,
            "description": "Folders not found",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Folders not found",
                        "code": "not_found",
                    }
                }
            },
        },
        **COMMON_ERROR_RESPONSES,
    },
)
async def get_folders() -> FoldersResponse:
    """List available mail folders."""
    try:
        folders = await imap.list_mailboxes()
        return FoldersResponse(folders=folders)
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
        200: {"content": {"application/json": {"example": {"message": "Email moved"}}}},
        404: {
            "model": ErrorResponse,
            "description": "Email not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Email not found", "code": "not_found"}
                }
            },
        },
        **COMMON_ERROR_RESPONSES,
    },
)
async def move_email(
    uid: str = Path(..., description="UID of the email to move"),
    folder: str = Query(..., description="Destination folder"),
    source_folder: str = Query("INBOX", description="Source folder"),
) -> MessageResponse:
    """Move an email to a different folder."""
    return await move_email_action(uid, folder, source_folder)


@read_router.post(
    "/emails/{uid}/forward",
    dependencies=[Security(get_api_key)],
    summary="Forward an email",
    description="Forward an existing email to new recipients.",
    response_model=MessageResponse,
    operation_id="forward_email",
    responses={
        200: {
            "content": {"application/json": {"example": {"message": "Email forwarded"}}}
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
        **COMMON_ERROR_RESPONSES,
    },
)
async def forward_email(
    uid: str = Path(..., description="UID of the email to forward"),
    request: SendEmailRequest = Body(
        ...,
        examples=[
            {
                "summary": "Forward email",
                "value": {
                    "to_addresses": ["recipient@example.com"],
                    "subject": "Fwd: Greetings",
                    "body": "See attached",
                },
            }
        ],
    ),
    folder: str = Query("INBOX", description="Mail folder to read from"),
) -> MessageResponse:
    """Forward an existing email to new recipients."""
    try:
        original = await imap.fetch_message(uid, folder)
        original_body = imap.extract_body(original)
        body = f"{request.body}\n\n{original_body}" if request.body else original_body
        subject = request.subject or imap.decode_header_value(
            original.get("Subject", "")
        )
        msg_id = original.get("Message-ID")
        headers = {}
        if msg_id:
            headers["In-Reply-To"] = msg_id
            headers["References"] = msg_id
        file_urls = [str(url) for url in request.file_urls] if request.file_urls else None
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
        200: {"content": {"application/json": {"example": {"message": "Email sent"}}}},
        404: {
            "model": ErrorResponse,
            "description": "Email not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Email not found", "code": "not_found"}
                }
            },
        },
        **COMMON_ERROR_RESPONSES,
    },
)
async def reply_email(
    uid: str = Path(..., description="UID of the email to reply to"),
    request: SendEmailRequest = Body(
        ...,
        examples=[
            {
                "summary": "Reply to email",
                "value": {
                    "to_addresses": ["recipient@example.com"],
                    "subject": "Re: Greetings",
                    "body": "Thanks!",
                },
            }
        ],
    ),
    folder: str = Query("INBOX", description="Mail folder to read from"),
) -> MessageResponse:
    """Reply to an existing email."""
    try:
        original = await imap.fetch_message(uid, folder)
        body = request.body or imap.extract_body(original)
        subj = imap.decode_header_value(original.get("Subject", ""))
        subject = request.subject or f"Re: {subj}"
        msg_id = original.get("Message-ID")
        headers = {}
        if msg_id:
            headers["In-Reply-To"] = msg_id
            headers["References"] = msg_id
        file_urls = [str(url) for url in request.file_urls] if request.file_urls else None
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
            "content": {"application/json": {"example": {"message": "Email deleted"}}}
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
        **COMMON_ERROR_RESPONSES,
    },
)
async def delete_email(
    uid: str = Path(..., description="UID of the email to delete"),
    folder: str = Query("INBOX", description="Folder containing the email"),
) -> MessageResponse:
    """Delete an email from the specified folder."""
    return await delete_email_action(uid, folder)


@read_router.post(
    "/drafts",
    dependencies=[Security(get_api_key)],
    summary="Create a draft email",
    description="Store an email draft in the Drafts folder.",
    response_model=MessageResponse,
    operation_id="create_draft",
    responses={
        200: {
            "content": {"application/json": {"example": {"message": "Draft stored"}}}
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
        **COMMON_ERROR_RESPONSES,
    },
)
async def create_draft(
    request: SendEmailRequest = Body(
        ...,
        examples=[
            {
                "summary": "Draft email",
                "value": {
                    "to_addresses": ["recipient@example.com"],
                    "subject": "Draft",
                    "body": "Draft body",
                },
            }
        ],
    )
) -> MessageResponse:
    """Store an email draft in the Drafts folder."""
    return await create_draft_action(request)
