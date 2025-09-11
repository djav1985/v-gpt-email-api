# flake8: noqa
import os
import sys
from email.message import EmailMessage
from fastapi.testclient import TestClient
import imaplib
import pytest

os.environ["ACCOUNT_EMAIL"] = "user@example.com"
os.environ["ACCOUNT_PASSWORD"] = "password"
os.environ["ACCOUNT_SMTP_SERVER"] = "smtp.example.com"
os.environ["ACCOUNT_SMTP_PORT"] = "587"
os.environ["ACCOUNT_IMAP_SERVER"] = "imap.example.com"
os.environ["ACCOUNT_IMAP_PORT"] = "993"

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app  # noqa: E402
from app import dependencies  # noqa: E402


@pytest.fixture(autouse=True)
def setup_settings():
    dependencies.settings = dependencies.Config()
    yield
    dependencies.settings = None


client = TestClient(app)


def test_list_folders(monkeypatch):
    class DummyIMAP:
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

    monkeypatch.setattr(imaplib, "IMAP4_SSL", lambda *a, **k: DummyIMAP())
    response = client.get("/imap/folders")
    assert response.status_code == 200
    assert response.json() == ["INBOX", "Archive"]


def test_fetch_messages(monkeypatch):
    class DummyIMAP:
        def login(self, *args, **kwargs):
            pass

        def select(self, folder):
            pass

        def search(self, charset, criteria):
            return "OK", [b"1"]

        def uid(self, cmd, uid, spec):
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

    monkeypatch.setattr(imaplib, "IMAP4_SSL", lambda *a, **k: DummyIMAP())
    response = client.get("/imap/emails")
    assert response.status_code == 200
    data = response.json()
    assert data[0]["subject"] == "Test"


def test_fetch_message(monkeypatch):
    class DummyIMAP:
        def login(self, *args, **kwargs):
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

        def __exit__(self, *args):
            pass

    monkeypatch.setattr(imaplib, "IMAP4_SSL", lambda *a, **k: DummyIMAP())
    response = client.get("/imap/emails/1")
    assert response.status_code == 200
    assert response.json()["body"].strip() == "hi"
