# flake8: noqa
import os
import sys
from fastapi.testclient import TestClient

os.environ["ACCOUNT_EMAIL"] = "user@example.com"
os.environ["ACCOUNT_PASSWORD"] = "password"
os.environ["ACCOUNT_SMTP_SERVER"] = "smtp.example.com"
os.environ["ACCOUNT_SMTP_PORT"] = "587"
os.environ["ACCOUNT_IMAP_SERVER"] = "imap.example.com"
os.environ["ACCOUNT_IMAP_PORT"] = "993"

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app  # noqa: E402
from app.services import imap_client
from app.models import EmailSummary
from app import dependencies
from datetime import datetime
from app.routes import read_email

dependencies.settings = dependencies.Config()
client = TestClient(app)


def test_get_folders(monkeypatch):
    async def mock_list_mailboxes():
        return ["INBOX", "Archive"]

    monkeypatch.setattr(imap_client, "list_mailboxes", mock_list_mailboxes)
    response = client.get("/folders")
    assert response.status_code == 200
    assert response.json() == ["INBOX", "Archive"]


def test_get_emails(monkeypatch):
    sample = [EmailSummary(uid="1", subject="Test", from_="a@example.com", date=datetime.utcnow(), seen=False)]

    async def mock_fetch_messages(folder: str, limit: int, unread_only: bool):
        return sample

    monkeypatch.setattr(imap_client, "fetch_messages", mock_fetch_messages)
    response = client.get("/emails?folder=INBOX&limit=1")
    assert response.status_code == 200
    data = response.json()
    assert data[0]["uid"] == "1"


def test_move_email(monkeypatch):
    called = {}

    async def mock_move(uid, folder, source_folder):
        called["uid"] = uid
        called["folder"] = folder
        called["source"] = source_folder

    monkeypatch.setattr(imap_client, "move_message", mock_move)
    response = client.post("/emails/1/move?folder=Archive&source_folder=Old")
    assert response.status_code == 200
    assert called == {"uid": "1", "folder": "Archive", "source": "Old"}
    assert response.json() == {"message": "Email moved"}


def test_delete_email(monkeypatch):
    called = {}

    async def mock_delete(uid, folder):
        called["uid"] = uid
        called["folder"] = folder

    monkeypatch.setattr(imap_client, "delete_message", mock_delete)
    response = client.delete("/emails/2?folder=INBOX")
    assert response.status_code == 200
    assert called == {"uid": "2", "folder": "INBOX"}
    assert response.json() == {"message": "Email deleted"}


def test_forward_email(monkeypatch):
    class DummyMessage:
        def __init__(self):
            self.headers = {"Message-ID": "<1@example.com>", "Subject": "Original"}
        def get(self, key, default=""):
            return self.headers.get(key, default)

    async def mock_fetch(uid):
        return DummyMessage()

    sent = {}

    async def mock_send(to, subject, body, file_url, headers):
        sent.update({"to": to, "subject": subject, "body": body, "headers": headers})

    monkeypatch.setattr(imap_client, "fetch_message", mock_fetch)
    monkeypatch.setattr(imap_client, "extract_body", lambda msg: "body")
    monkeypatch.setattr(imap_client, "decode_header_value", lambda v: v)
    monkeypatch.setattr("app.routes.read_email.send_email", mock_send)
    response = client.post(
        "/emails/1/forward",
        json={"to_addresses": ["a@b.com"], "subject": "S", "body": "B", "file_url": None},
    )
    assert response.status_code == 200
    assert sent["subject"] == "S"
    assert sent["body"] == "body"
    assert sent["headers"]["In-Reply-To"] == "<1@example.com>"
    assert sent["headers"]["References"] == "<1@example.com>"
    assert response.json() == {"message": "Email forwarded"}


def test_reply_email(monkeypatch):
    class DummyMessage:
        def __init__(self):
            self.headers = {"Message-ID": "<2@example.com>", "Subject": "Orig"}
        def get(self, key, default=""):
            return self.headers.get(key, default)

    async def mock_fetch(uid):
        return DummyMessage()

    sent = {}

    async def mock_send(to, subject, body, file_url, headers):
        sent.update({"to": to, "subject": subject, "body": body, "headers": headers})

    monkeypatch.setattr(imap_client, "fetch_message", mock_fetch)
    monkeypatch.setattr(imap_client, "extract_body", lambda msg: "orig body")
    monkeypatch.setattr(imap_client, "decode_header_value", lambda v: v)
    monkeypatch.setattr("app.routes.read_email.send_email", mock_send)
    response = client.post(
        "/emails/2/reply",
        json={"to_addresses": ["a@b.com"], "subject": "S", "body": "B", "file_url": None},
    )
    assert response.status_code == 200
    assert sent["subject"] == "S"
    assert sent["body"] == "B"
    assert sent["headers"]["In-Reply-To"] == "<2@example.com>"
    assert response.json() == {"message": "Email sent"}


def test_create_draft(monkeypatch):
    called = {}

    async def mock_append(folder, msg):
        called["folder"] = folder

    monkeypatch.setattr(imap_client, "append_message", mock_append)
    response = client.post(
        "/drafts",
        json={"to_addresses": ["x@y.com"], "subject": "S", "body": "B", "file_url": None},
    )
    assert response.status_code == 200
    assert called["folder"] == "Drafts"
    assert response.json() == {"message": "Draft stored"}

def test_get_folders_error(monkeypatch):
    async def fail():
        raise RuntimeError("boom")
    monkeypatch.setattr(imap_client, "list_mailboxes", fail)
    resp = client.get("/folders")
    assert resp.status_code == 500


def test_get_emails_error(monkeypatch):
    async def fail(folder, limit, unread_only):
        raise RuntimeError("boom")
    monkeypatch.setattr(imap_client, "fetch_messages", fail)
    resp = client.get("/emails")
    assert resp.status_code == 500


def test_move_email_error(monkeypatch):
    async def fail(uid, folder, source_folder):
        raise RuntimeError("boom")
    monkeypatch.setattr(imap_client, "move_message", fail)
    resp = client.post("/emails/1/move?folder=Archive")
    assert resp.status_code == 500


def test_create_draft_missing_settings(monkeypatch):
    monkeypatch.setattr(dependencies, "settings", None)
    resp = client.post(
        "/drafts",
        json={"to_addresses": ["x@y.com"], "subject": "S", "body": "B", "file_url": None},
    )
    assert resp.status_code == 500
