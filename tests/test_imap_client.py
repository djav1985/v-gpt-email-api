# flake8: noqa
import os
import sys
import asyncio
from datetime import datetime
import imaplib
import pytest
from email.message import EmailMessage

os.environ["ACCOUNT_EMAIL"] = "user@example.com"
os.environ["ACCOUNT_PASSWORD"] = "password"
os.environ["ACCOUNT_SMTP_SERVER"] = "smtp.example.com"
os.environ["ACCOUNT_SMTP_PORT"] = "587"
os.environ["ACCOUNT_IMAP_SERVER"] = "imap.example.com"
os.environ["ACCOUNT_IMAP_PORT"] = "993"

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services import imap_client
from app import dependencies


class DummyIMAPList:
    def login(self, *args, **kwargs):
        pass

    def list(self):
        return "OK", [
            b'(\\HasNoChildren) "/" "INBOX"',
            b'(\\HasNoChildren) "/" "My Stuff"',
            b'(\\HasNoChildren) "/" "My Quoted Folder"',
        ]

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


def test_list_mailboxes_parsing(monkeypatch):
    dependencies.settings = dependencies.Config()
    imap_client.settings = dependencies.settings
    monkeypatch.setattr(imaplib, "IMAP4_SSL", lambda *args, **kwargs: DummyIMAPList())
    mailboxes = asyncio.run(imap_client.list_mailboxes())
    assert mailboxes == ["INBOX", "My Stuff", "My Quoted Folder"]


class DummyIMAPFetch:
    def login(self, *args, **kwargs):
        pass

    def select(self, folder):
        assert folder == "INBOX"

    def search(self, charset, criteria):
        return "OK", [b"1"]

    def uid(self, cmd, uid, args):
        if cmd == "fetch":
            msg = EmailMessage()
            msg["Subject"] = "=?utf-8?B?VGVzdA==?= =?utf-8?B?IG11bHRp?= =?utf-8?B?LXBhcnQ=?="
            msg["From"] = "=?utf-8?B?Sm9obiBEb2U=?= <john@example.com>"
            msg["Date"] = "Mon, 02 Oct 2023 13:00:00 +0000"
            return "OK", [(b"1 (FLAGS (\\Seen))", bytes(msg))]
        return "NO", []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


def test_fetch_messages_decoding(monkeypatch):
    dependencies.settings = dependencies.Config()
    imap_client.settings = dependencies.settings
    monkeypatch.setattr(imaplib, "IMAP4_SSL", lambda *args, **kwargs: DummyIMAPFetch())
    summaries = asyncio.run(imap_client.fetch_messages())
    assert summaries[0].subject == "Test multi-part"
    assert isinstance(summaries[0].date, datetime)
