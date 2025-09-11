import asyncio
import email
import imaplib
import re
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import parsedate_to_datetime

from fastapi import APIRouter, HTTPException, Query, Path, Body, Security

from .. import dependencies
from ..dependencies import get_api_key
from ..models import EmailSummary, MessageResponse, SendEmailRequest


def _decode_header(value: str) -> str:
    parts = email.header.decode_header(value)
    decoded = []
    for part, enc in parts:
        if isinstance(part, bytes):
            decoded.append(part.decode(enc or "utf-8", errors="ignore"))
        else:
            decoded.append(part)
    return "".join(decoded)


def decode_header_value(value: str) -> str:
    return _decode_header(value)


def _extract_body(msg: email.message.Message) -> str:
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain" and not part.get_filename():
                payload = part.get_payload(decode=True)
                return payload.decode(
                    part.get_content_charset() or "utf-8", errors="ignore"
                )
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            return payload.decode(msg.get_content_charset() or "utf-8", errors="ignore")
    return ""


def extract_body(msg: email.message.Message) -> str:
    return _extract_body(msg)


async def list_mailboxes() -> list[str]:
    """Return a list of mailbox names."""

    def inner() -> list[str]:
        if dependencies.settings is None:
            raise RuntimeError("Settings have not been initialized")
        with imaplib.IMAP4_SSL(
            dependencies.settings.account_imap_server,
            dependencies.settings.account_imap_port,
        ) as imap:
            imap.login(
                dependencies.settings.account_email,
                dependencies.settings.account_password,
            )
            typ, data = imap.list()
            if typ != "OK" or data is None:
                return []
            mailboxes: list[str] = []
            for mbox in data:
                line = mbox.decode()
                match = re.search(r'"((?:\\"|[^"])*)"$', line)
                if match:
                    name = match.group(1).replace('\\"', '"')
                else:
                    name = line.split()[-1]
                mailboxes.append(name)
            return mailboxes

    return await asyncio.to_thread(inner)


async def fetch_messages(
    folder: str = "INBOX", limit: int = 10, unread_only: bool = False
) -> list[EmailSummary]:
    """Fetch message headers from a folder and return summaries."""

    def inner() -> list[EmailSummary]:
        if dependencies.settings is None:
            raise RuntimeError("Settings have not been initialized")
        with imaplib.IMAP4_SSL(
            dependencies.settings.account_imap_server,
            dependencies.settings.account_imap_port,
        ) as imap:
            imap.login(
                dependencies.settings.account_email,
                dependencies.settings.account_password,
            )
            imap.select(folder)
            criteria = "UNSEEN" if unread_only else "ALL"
            typ, data = imap.search(None, criteria)
            if typ != "OK" or not data or not data[0]:
                return []
            uids = data[0].split()
            if limit:
                uids = uids[-limit:]
            summaries: list[EmailSummary] = []
            for uid in uids:
                typ, msg_data = imap.uid("fetch", uid, "(RFC822.HEADER FLAGS)")
                if typ != "OK" or msg_data is None:
                    continue
                header_bytes = msg_data[0][1]
                flag_info = msg_data[0][0].decode()
                msg = email.message_from_bytes(header_bytes)
                subject = _decode_header(msg.get("Subject", ""))
                from_raw = _decode_header(msg.get("From", ""))
                from_ = email.utils.parseaddr(from_raw)[1]
                date_raw = msg.get("Date", "")
                date = parsedate_to_datetime(date_raw) if date_raw else None
                seen = "\\Seen" in flag_info
                summaries.append(
                    EmailSummary(
                        uid=uid.decode(),
                        subject=subject or "",
                        from_=from_,
                        date=date,
                        seen=seen,
                    )
                )
            return summaries

    return await asyncio.to_thread(inner)


async def move_message(uid: str, folder: str, source_folder: str = "INBOX") -> None:
    """Move a message to another folder."""

    def inner() -> None:
        if dependencies.settings is None:
            raise RuntimeError("Settings have not been initialized")
        with imaplib.IMAP4_SSL(
            dependencies.settings.account_imap_server,
            dependencies.settings.account_imap_port,
        ) as imap:
            imap.login(
                dependencies.settings.account_email,
                dependencies.settings.account_password,
            )
            imap.select(source_folder)
            imap.uid("COPY", uid, folder)
            imap.uid("STORE", uid, "+FLAGS", "(\\Deleted)")
            imap.expunge()

    await asyncio.to_thread(inner)


async def delete_message(uid: str, folder: str = "INBOX") -> None:
    """Delete a message from a folder."""

    def inner() -> None:
        if dependencies.settings is None:
            raise RuntimeError("Settings have not been initialized")
        with imaplib.IMAP4_SSL(
            dependencies.settings.account_imap_server,
            dependencies.settings.account_imap_port,
        ) as imap:
            imap.login(
                dependencies.settings.account_email,
                dependencies.settings.account_password,
            )
            imap.select(folder)
            imap.uid("STORE", uid, "+FLAGS", "(\\Deleted)")
            imap.expunge()

    await asyncio.to_thread(inner)


async def append_message(folder: str, msg: MIMEMultipart) -> None:
    """Append a raw message to the specified folder."""

    def inner() -> None:
        if dependencies.settings is None:
            raise RuntimeError("Settings have not been initialized")
        with imaplib.IMAP4_SSL(
            dependencies.settings.account_imap_server,
            dependencies.settings.account_imap_port,
        ) as imap:
            imap.login(
                dependencies.settings.account_email,
                dependencies.settings.account_password,
            )
            imap.append(
                folder, "", imaplib.Time2Internaldate(time.time()), msg.as_bytes()
            )

    await asyncio.to_thread(inner)


async def fetch_message(uid: str, folder: str = "INBOX") -> email.message.Message:
    """Fetch a full message by UID."""

    def inner() -> email.message.Message:
        if dependencies.settings is None:
            raise RuntimeError("Settings have not been initialized")
        with imaplib.IMAP4_SSL(
            dependencies.settings.account_imap_server,
            dependencies.settings.account_imap_port,
        ) as imap:
            imap.login(
                dependencies.settings.account_email,
                dependencies.settings.account_password,
            )
            imap.select(folder)
            typ, msg_data = imap.uid("fetch", uid, "(RFC822)")
            if typ != "OK" or msg_data is None or not msg_data[0]:
                raise RuntimeError("Failed to fetch message")
            return email.message_from_bytes(msg_data[0][1])

    return await asyncio.to_thread(inner)


async def move_email_action(
    uid: str, folder: str, source_folder: str = "INBOX"
) -> MessageResponse:
    try:
        await move_message(uid, folder, source_folder)
        return MessageResponse(message="Email moved")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def delete_email_action(uid: str, folder: str = "INBOX") -> MessageResponse:
    try:
        await delete_message(uid, folder)
        return MessageResponse(message="Email deleted")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def create_draft_action(request: SendEmailRequest) -> MessageResponse:
    if dependencies.settings is None:
        raise HTTPException(
            status_code=500, detail="Settings have not been initialized"
        )
    msg = MIMEMultipart()
    msg["From"] = dependencies.settings.account_email
    msg["To"] = ", ".join(request.to_addresses)
    msg["Subject"] = request.subject
    msg.attach(MIMEText(request.body, "html"))
    try:
        await append_message("Drafts", msg)
        return MessageResponse(message="Draft stored")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


imap_router = APIRouter(prefix="/imap", tags=["IMAP"])


@imap_router.get("/folders", dependencies=[Security(get_api_key)])
async def get_folders() -> list[str]:
    try:
        return await list_mailboxes()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@imap_router.get(
    "/emails", response_model=list[EmailSummary], dependencies=[Security(get_api_key)]
)
async def get_emails(
    folder: str = Query("INBOX", description="Mail folder to read from"),
    limit: int = Query(10, gt=0, description="Maximum number of emails to return"),
    unread: bool = Query(False, description="Only fetch unread emails"),
) -> list[EmailSummary]:
    try:
        return await fetch_messages(folder, limit, unread)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@imap_router.post(
    "/emails/{uid}/move",
    dependencies=[Security(get_api_key)],
    response_model=MessageResponse,
)
async def move_email(
    uid: str = Path(..., description="UID of the email to move"),
    folder: str = Query(..., description="Destination folder"),
    source_folder: str = Query("INBOX", description="Source folder"),
) -> MessageResponse:
    return await move_email_action(uid, folder, source_folder)


@imap_router.delete(
    "/emails/{uid}",
    dependencies=[Security(get_api_key)],
    response_model=MessageResponse,
)
async def delete_email(
    uid: str = Path(...), folder: str = Query("INBOX")
) -> MessageResponse:
    return await delete_email_action(uid, folder)


@imap_router.get("/emails/{uid}", dependencies=[Security(get_api_key)])
async def get_email(uid: str = Path(...), folder: str = Query("INBOX")) -> dict:
    try:
        msg = await fetch_message(uid, folder)
        return {"body": extract_body(msg)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@imap_router.post(
    "/drafts", dependencies=[Security(get_api_key)], response_model=MessageResponse
)
async def create_draft(request: SendEmailRequest = Body(...)) -> MessageResponse:
    return await create_draft_action(request)
