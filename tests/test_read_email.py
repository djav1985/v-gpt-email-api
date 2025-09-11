from datetime import datetime

import pytest

from app.routes import imap
from app.models import EmailSummary
from app import dependencies


@pytest.mark.asyncio
async def test_get_folders(monkeypatch, client):
    async def mock_list_mailboxes():
        return ["INBOX", "Archive"]

    monkeypatch.setattr(imap, "list_mailboxes", mock_list_mailboxes)
    response = await client.get("/folders")
    assert response.status_code == 200
    assert response.json() == {"folders": ["INBOX", "Archive"]}


@pytest.mark.asyncio
async def test_get_emails(monkeypatch, client):
    sample = [
        EmailSummary(
            uid="1",
            subject="Test",
            from_="a@example.com",
            date=datetime.utcnow(),
            seen=False,
        )
    ]

    async def mock_fetch_messages(folder: str, limit: int, unread_only: bool):
        return sample

    monkeypatch.setattr(imap, "fetch_messages", mock_fetch_messages)
    response = await client.get("/emails?folder=INBOX&limit=1")
    assert response.status_code == 200
    data = response.json()
    assert data[0]["uid"] == "1"


@pytest.mark.asyncio
async def test_get_emails_negative_limit(client):
    resp = await client.get("/emails?limit=-1")
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_get_emails_missing_api_key(client):
    del client.headers["X-API-Key"]
    resp = await client.get("/emails")
    assert resp.status_code == 401
    client.headers["X-API-Key"] = "token"


@pytest.mark.asyncio
async def test_get_emails_invalid_api_key(monkeypatch, client):
    dependencies.settings.api_key = "expected"
    client.headers["X-API-Key"] = "wrong"
    resp = await client.get("/emails")
    assert resp.status_code == 401
    dependencies.settings.api_key = None
    client.headers["X-API-Key"] = "token"


@pytest.mark.asyncio
async def test_imap_emails_negative_limit(client):
    resp = await client.get("/imap/emails?limit=-1")
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_move_email(monkeypatch, client):
    called = {}

    async def mock_move(uid, folder, source_folder):
        called["uid"] = uid
        called["folder"] = folder
        called["source"] = source_folder

    monkeypatch.setattr(imap, "move_message", mock_move)
    response = await client.post("/emails/1/move?folder=Archive&source_folder=Old")
    assert response.status_code == 200
    assert called == {"uid": "1", "folder": "Archive", "source": "Old"}
    assert response.json() == {"message": "Email moved"}


@pytest.mark.asyncio
async def test_delete_email(monkeypatch, client):
    called = {}

    async def mock_delete(uid, folder):
        called["uid"] = uid
        called["folder"] = folder

    monkeypatch.setattr(imap, "delete_message", mock_delete)
    response = await client.delete("/emails/2?folder=INBOX")
    assert response.status_code == 200
    assert called == {"uid": "2", "folder": "INBOX"}
    assert response.json() == {"message": "Email deleted"}


@pytest.mark.asyncio
async def test_forward_email(monkeypatch, client):
    class DummyMessage:
        def __init__(self):
            self.headers = {"Message-ID": "<1@example.com>", "Subject": "Original"}

        def get(self, key, default=""):
            return self.headers.get(key, default)

    async def mock_fetch(uid, folder="INBOX"):
        return DummyMessage()

    sent = {}

    async def mock_send(to, subject, body, file_urls, headers):
        sent.update(
            {
                "to": to,
                "subject": subject,
                "body": body,
                "headers": headers,
                "files": file_urls,
            }
        )

    monkeypatch.setattr(imap, "fetch_message", mock_fetch)
    monkeypatch.setattr(imap, "extract_body", lambda msg: "body")
    monkeypatch.setattr(imap, "decode_header_value", lambda v: v)
    monkeypatch.setattr("app.routes.read_email.send_email", mock_send)
    response = await client.post(
        "/emails/1/forward",
        json={
            "to_addresses": ["a@b.com"],
            "subject": "S",
            "body": "B",
            "file_urls": None,
        },
    )
    assert response.status_code == 200
    assert sent["subject"] == "S"
    assert sent["body"] == "B\n\nbody"
    assert sent["headers"]["In-Reply-To"] == "<1@example.com>"
    assert sent["headers"]["References"] == "<1@example.com>"
    assert response.json() == {"message": "Email forwarded"}


@pytest.mark.asyncio
async def test_reply_email(monkeypatch, client):
    class DummyMessage:
        def __init__(self):
            self.headers = {"Message-ID": "<2@example.com>", "Subject": "Orig"}

        def get(self, key, default=""):
            return self.headers.get(key, default)

    async def mock_fetch(uid, folder="INBOX"):
        return DummyMessage()

    sent = {}

    async def mock_send(to, subject, body, file_urls, headers):
        sent.update(
            {
                "to": to,
                "subject": subject,
                "body": body,
                "headers": headers,
                "files": file_urls,
            }
        )

    monkeypatch.setattr(imap, "fetch_message", mock_fetch)
    monkeypatch.setattr(imap, "extract_body", lambda msg: "orig body")
    monkeypatch.setattr(imap, "decode_header_value", lambda v: v)
    monkeypatch.setattr("app.routes.read_email.send_email", mock_send)
    response = await client.post(
        "/emails/2/reply",
        json={
            "to_addresses": ["a@b.com"],
            "subject": "S",
            "body": "B",
            "file_urls": None,
        },
    )
    assert response.status_code == 200
    assert sent["subject"] == "S"
    assert sent["body"] == "B"
    assert sent["headers"]["In-Reply-To"] == "<2@example.com>"
    assert response.json() == {"message": "Email sent"}


@pytest.mark.asyncio
async def test_create_draft(monkeypatch, client):
    called = {}

    async def mock_append(folder, msg):
        called["folder"] = folder

    monkeypatch.setattr(imap, "append_message", mock_append)
    response = await client.post(
        "/drafts",
        json={
            "to_addresses": ["x@y.com"],
            "subject": "S",
            "body": "B",
            "file_urls": None,
        },
    )
    assert response.status_code == 200
    assert called["folder"] == "Drafts"
    assert response.json() == {"message": "Draft stored"}


@pytest.mark.asyncio
async def test_get_folders_error(monkeypatch, client):
    async def fail():
        raise RuntimeError("boom")

    monkeypatch.setattr(imap, "list_mailboxes", fail)
    resp = await client.get("/folders")
    assert resp.status_code == 500


@pytest.mark.asyncio
async def test_get_emails_error(monkeypatch, client):
    async def fail(folder, limit, unread_only):
        raise RuntimeError("boom")

    monkeypatch.setattr(imap, "fetch_messages", fail)
    resp = await client.get("/emails")
    assert resp.status_code == 500


@pytest.mark.asyncio
async def test_move_email_error(monkeypatch, client):
    async def fail(uid, folder, source_folder):
        raise RuntimeError("boom")

    monkeypatch.setattr(imap, "move_message", fail)
    resp = await client.post("/emails/1/move?folder=Archive")
    assert resp.status_code == 500


@pytest.mark.asyncio
async def test_create_draft_missing_settings(monkeypatch, client):
    monkeypatch.setattr(dependencies, "settings", None)
    resp = await client.post(
        "/drafts",
        json={
            "to_addresses": ["x@y.com"],
            "subject": "S",
            "body": "B",
            "file_urls": None,
        },
    )
    assert resp.status_code == 500
