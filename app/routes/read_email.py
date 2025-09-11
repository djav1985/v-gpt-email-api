# flake8: noqa
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from fastapi import APIRouter, Depends, HTTPException

from ..dependencies import get_api_key, send_email, settings
from ..models import SendEmailRequest, EmailSummary
from ..services import imap_client

read_router = APIRouter()


@read_router.get("/emails", response_model=list[EmailSummary], dependencies=[Depends(get_api_key)])
async def get_emails(limit: int = 10, unread: bool = False, folder: str = "INBOX") -> list[EmailSummary]:
    """Return emails from the specified folder."""
    try:
        return await imap_client.fetch_messages(folder, limit, unread)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@read_router.get("/folders", dependencies=[Depends(get_api_key)])
async def get_folders() -> list[str]:
    """List available mail folders."""
    try:
        return await imap_client.list_mailboxes()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@read_router.post("/emails/{uid}/move", dependencies=[Depends(get_api_key)])
async def move_email(uid: str, folder: str, source_folder: str = "INBOX") -> dict[str, str]:
    try:
        await imap_client.move_message(uid, folder, source_folder)
        return {"message": "Email moved"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@read_router.post("/emails/{uid}/forward", dependencies=[Depends(get_api_key)])
async def forward_email(uid: str, request: SendEmailRequest) -> dict[str, str]:
    try:
        original = await imap_client.fetch_message(uid)
        body = imap_client.extract_body(original)
        subject = request.subject or imap_client.decode_header_value(original.get("Subject", ""))
        msg_id = original.get("Message-ID")
        headers = {}
        if msg_id:
            headers["In-Reply-To"] = msg_id
            headers["References"] = msg_id
        await send_email(request.to_addresses, subject, body, request.file_url, headers=headers)
        return {"message": "Email forwarded"}
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@read_router.post("/emails/{uid}/reply", dependencies=[Depends(get_api_key)])
async def reply_email(uid: str, request: SendEmailRequest) -> dict[str, str]:
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
        await send_email(request.to_addresses, subject, body, request.file_url, headers=headers)
        return {"message": "Email sent"}
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@read_router.delete("/emails/{uid}", dependencies=[Depends(get_api_key)])
async def delete_email(uid: str, folder: str = "INBOX") -> dict[str, str]:
    try:
        await imap_client.delete_message(uid, folder)
        return {"message": "Email deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@read_router.post("/drafts", dependencies=[Depends(get_api_key)])
async def create_draft(request: SendEmailRequest) -> dict[str, str]:
    if settings is None:
        raise HTTPException(status_code=500, detail="Settings have not been initialized")
    msg = MIMEMultipart()
    msg["From"] = settings.account_email
    msg["To"] = ", ".join(request.to_addresses)
    msg["Subject"] = request.subject
    msg.attach(MIMEText(request.body, "html"))
    try:
        await imap_client.append_message("Drafts", msg)
        return {"message": "Draft stored"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
