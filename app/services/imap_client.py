import asyncio
import imaplib
import email
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from ..dependencies import settings
from ..models import EmailSummary


async def list_mailboxes() -> list[str]:
    """Return a list of mailbox names."""

    def inner() -> list[str]:
        if settings is None:
            raise RuntimeError("Settings have not been initialized")
        with imaplib.IMAP4_SSL(settings.account_imap_server, settings.account_imap_port) as imap:
            imap.login(settings.account_email, settings.account_password)
            typ, data = imap.list()
            if typ != "OK" or data is None:
                return []
            mailboxes: list[str] = []
            for mbox in data:
                parts = mbox.decode().split(' "" "')
                if len(parts) > 1:
                    mailboxes.append(parts[-1].strip('"'))
                else:
                    mailboxes.append(mbox.decode())
            return mailboxes

    return await asyncio.to_thread(inner)


async def fetch_messages(folder: str = "INBOX", limit: int = 10, unread_only: bool = False) -> list[EmailSummary]:
    """Fetch message headers from a folder and return summaries."""

    def inner() -> list[EmailSummary]:
        if settings is None:
            raise RuntimeError("Settings have not been initialized")
        with imaplib.IMAP4_SSL(settings.account_imap_server, settings.account_imap_port) as imap:
            imap.login(settings.account_email, settings.account_password)
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
                typ, msg_data = imap.uid('fetch', uid, '(RFC822.HEADER FLAGS)')
                if typ != "OK" or msg_data is None:
                    continue
                header_bytes = msg_data[0][1]
                flag_info = msg_data[0][0].decode()
                msg = email.message_from_bytes(header_bytes)
                subject, _ = email.header.decode_header(msg.get('Subject', ''))[0]
                if isinstance(subject, bytes):
                    subject = subject.decode(errors='ignore')
                from_ = email.utils.parseaddr(msg.get('From', ''))[1]
                date = msg.get('Date', '')
                seen = "\\Seen" in flag_info
                summaries.append(EmailSummary(uid=uid.decode(), subject=subject or "", from_=from_, date=date or "", seen=seen))
            return summaries

    return await asyncio.to_thread(inner)


async def move_message(uid: str, folder: str) -> None:
    """Move a message to another folder."""

    def inner() -> None:
        if settings is None:
            raise RuntimeError("Settings have not been initialized")
        with imaplib.IMAP4_SSL(settings.account_imap_server, settings.account_imap_port) as imap:
            imap.login(settings.account_email, settings.account_password)
            imap.select("INBOX")
            imap.uid("COPY", uid, folder)
            imap.uid("STORE", uid, "+FLAGS", "(\\Deleted)")
            imap.expunge()

    await asyncio.to_thread(inner)


async def delete_message(uid: str, folder: str = "INBOX") -> None:
    """Delete a message from a folder."""

    def inner() -> None:
        if settings is None:
            raise RuntimeError("Settings have not been initialized")
        with imaplib.IMAP4_SSL(settings.account_imap_server, settings.account_imap_port) as imap:
            imap.login(settings.account_email, settings.account_password)
            imap.select(folder)
            imap.uid("STORE", uid, "+FLAGS", "(\\Deleted)")
            imap.expunge()

    await asyncio.to_thread(inner)


async def append_message(folder: str, msg: MIMEMultipart) -> None:
    """Append a raw message to the specified folder."""

    def inner() -> None:
        if settings is None:
            raise RuntimeError("Settings have not been initialized")
        with imaplib.IMAP4_SSL(settings.account_imap_server, settings.account_imap_port) as imap:
            imap.login(settings.account_email, settings.account_password)
            imap.append(folder, "", imaplib.Time2Internaldate(time.time()), msg.as_bytes())

    await asyncio.to_thread(inner)
