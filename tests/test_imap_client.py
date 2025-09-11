# flake8: noqa
import asyncio
import os
import sys
from datetime import datetime
from email.message import EmailMessage, Message
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import imaplib
import pytest

os.environ["ACCOUNT_EMAIL"] = "user@example.com"
os.environ["ACCOUNT_PASSWORD"] = "password"
os.environ["ACCOUNT_SMTP_SERVER"] = "smtp.example.com"
os.environ["ACCOUNT_SMTP_PORT"] = "587"
os.environ["ACCOUNT_IMAP_SERVER"] = "imap.example.com"
os.environ["ACCOUNT_IMAP_PORT"] = "993"

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services import imap_client  # noqa: E402
from app import dependencies  # noqa: E402


@pytest.fixture(autouse=True)
def setup_settings():
    dependencies.settings = dependencies.Config()
    imap_client.settings = dependencies.settings
    yield
    dependencies.settings = None


def test_decode_header_value():
    encoded = "=?utf-8?B?VGVzdA==?="
    assert imap_client.decode_header_value(encoded) == "Test"


def test_extract_body_plain():
    msg = EmailMessage()
    msg.set_content("hello")
    assert imap_client.extract_body(msg).strip() == "hello"


def test_extract_body_multipart():
    msg = MIMEMultipart()
    msg.attach(MIMEText("plain", "plain"))
    msg.attach(MIMEText("<b>html</b>", "html"))
    assert imap_client.extract_body(msg).strip() == "plain"


class DummyIMAPList:
    def login(self, *args, **kwargs):
        pass

    def list(self):
        return "OK", [
            b'(\\HasNoChildren) "/" "INBOX"',
            b'(\\HasNoChildren) "/" "Archive"',
        ]

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


def test_list_mailboxes(monkeypatch):
    monkeypatch.setattr(imaplib, "IMAP4_SSL", lambda *a, **k: DummyIMAPList())
    boxes = asyncio.run(imap_client.list_mailboxes())
    assert boxes == ["INBOX", "Archive"]


class DummyIMAPListFail:
    def login(self, *args, **kwargs):
        pass

    def list(self):
        return "NO", None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


def test_list_mailboxes_failure(monkeypatch):
    monkeypatch.setattr(imaplib, "IMAP4_SSL", lambda *a, **k: DummyIMAPListFail())
    boxes = asyncio.run(imap_client.list_mailboxes())
    assert boxes == []


class DummyIMAPFetch:
    def login(self, *args, **kwargs):
        pass

    def select(self, folder):
        pass

    def search(self, charset, criteria):
        return "OK", [b"1"]

    def uid(self, cmd, uid, args):
        if cmd == "fetch":
            msg = EmailMessage()
            msg["Subject"] = "=?utf-8?B?VGVzdA==?="
            msg["From"] = "test@example.com"
            msg["Date"] = "Mon, 02 Oct 2023 13:00:00 +0000"
            return "OK", [(b"1 (FLAGS (\\Seen))", bytes(msg))]
        return "NO", []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


def test_fetch_messages(monkeypatch):
    monkeypatch.setattr(imaplib, "IMAP4_SSL", lambda *a, **k: DummyIMAPFetch())
    summaries = asyncio.run(imap_client.fetch_messages())
    assert summaries[0].subject == "Test"


class DummyIMAPFetchFail:
    def login(self, *args, **kwargs):
        pass

    def select(self, folder):
        pass

    def search(self, charset, criteria):
        return "NO", None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


def test_fetch_messages_failure(monkeypatch):
    monkeypatch.setattr(imaplib, "IMAP4_SSL", lambda *a, **k: DummyIMAPFetchFail())
    summaries = asyncio.run(imap_client.fetch_messages())
    assert summaries == []


class DummyIMAPMove:
    def __init__(self):
        self.copied = False
        self.deleted = False

    def login(self, *a, **k):
        pass

    def select(self, folder):
        self.folder = folder

    def uid(self, cmd, uid, *args):
        if cmd == "COPY":
            self.copied = True
        elif cmd == "STORE":
            self.deleted = True

    def expunge(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *a):
        pass


def test_move_message(monkeypatch):
    dummy = DummyIMAPMove()
    monkeypatch.setattr(imaplib, "IMAP4_SSL", lambda *a, **k: dummy)
    asyncio.run(imap_client.move_message("1", "Dest", "INBOX"))
    assert dummy.copied and dummy.deleted


class DummyIMAPMoveFail:
    def login(self, *a, **k):
        pass

    def select(self, folder):
        pass

    def uid(self, *a, **k):
        raise RuntimeError("fail")

    def __enter__(self):
        return self

    def __exit__(self, *a):
        pass


def test_move_message_failure(monkeypatch):
    monkeypatch.setattr(imaplib, "IMAP4_SSL", lambda *a, **k: DummyIMAPMoveFail())
    with pytest.raises(RuntimeError):
        asyncio.run(imap_client.move_message("1", "Dest", "INBOX"))


class DummyIMAPDelete:
    def login(self, *a, **k):
        pass

    def select(self, folder):
        pass

    def uid(self, *a, **k):
        pass

    def expunge(self):
        self.expunge_called = True

    def __enter__(self):
        return self

    def __exit__(self, *a):
        pass


def test_delete_message(monkeypatch):
    dummy = DummyIMAPDelete()
    monkeypatch.setattr(imaplib, "IMAP4_SSL", lambda *a, **k: dummy)
    asyncio.run(imap_client.delete_message("1"))
    assert dummy.expunge_called


class DummyIMAPDeleteFail:
    def login(self, *a, **k):
        pass

    def select(self, folder):
        pass

    def uid(self, *a, **k):
        raise RuntimeError("fail")

    def __enter__(self):
        return self

    def __exit__(self, *a):
        pass


def test_delete_message_failure(monkeypatch):
    monkeypatch.setattr(imaplib, "IMAP4_SSL", lambda *a, **k: DummyIMAPDeleteFail())
    with pytest.raises(RuntimeError):
        asyncio.run(imap_client.delete_message("1"))


class DummyIMAPAppend:
    def login(self, *a, **k):
        pass

    def append(self, folder, flags, date, data):
        self.appended = True

    def __enter__(self):
        return self

    def __exit__(self, *a):
        pass


def test_append_message(monkeypatch):
    dummy = DummyIMAPAppend()
    monkeypatch.setattr(imaplib, "IMAP4_SSL", lambda *a, **k: dummy)
    msg = MIMEMultipart()
    asyncio.run(imap_client.append_message("Drafts", msg))
    assert dummy.appended


class DummyIMAPAppendFail:
    def login(self, *a, **k):
        pass

    def append(self, *a, **k):
        raise RuntimeError("fail")

    def __enter__(self):
        return self

    def __exit__(self, *a):
        pass


def test_append_message_failure(monkeypatch):
    monkeypatch.setattr(imaplib, "IMAP4_SSL", lambda *a, **k: DummyIMAPAppendFail())
    msg = MIMEMultipart()
    with pytest.raises(RuntimeError):
        asyncio.run(imap_client.append_message("Drafts", msg))


class DummyIMAPFetchMsg:
    def login(self, *a, **k):
        pass

    def select(self, folder):
        pass

    def uid(self, cmd, uid, spec):
        if cmd == "fetch":
            msg = EmailMessage()
            msg.set_content("hi")
            return "OK", [(None, msg.as_bytes())]
        return "NO", []

    def __enter__(self):
        return self

    def __exit__(self, *a):
        pass


def test_fetch_message(monkeypatch):
    monkeypatch.setattr(imaplib, "IMAP4_SSL", lambda *a, **k: DummyIMAPFetchMsg())
    msg = asyncio.run(imap_client.fetch_message("1"))
    assert isinstance(msg, Message)


class DummyIMAPFetchMsgFail:
    def login(self, *a, **k):
        pass

    def select(self, folder):
        pass

    def uid(self, *a, **k):
        return "NO", None

    def __enter__(self):
        return self

    def __exit__(self, *a):
        pass


def test_fetch_message_failure(monkeypatch):
    monkeypatch.setattr(imaplib, "IMAP4_SSL", lambda *a, **k: DummyIMAPFetchMsgFail())
    with pytest.raises(RuntimeError):
        asyncio.run(imap_client.fetch_message("1"))
