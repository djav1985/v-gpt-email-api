import os
import sys
from fastapi.testclient import TestClient
import pytest

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

client = TestClient(app)


def test_get_folders(monkeypatch):
    async def mock_list_mailboxes():
        return ["INBOX", "Archive"]

    monkeypatch.setattr(imap_client, "list_mailboxes", mock_list_mailboxes)
    response = client.get("/folders")
    assert response.status_code == 200
    assert response.json() == ["INBOX", "Archive"]


def test_get_emails(monkeypatch):
    sample = [EmailSummary(uid="1", subject="Test", from_="a@example.com", date="today", seen=False)]

    async def mock_fetch_messages(folder: str, limit: int, unread_only: bool):
        return sample

    monkeypatch.setattr(imap_client, "fetch_messages", mock_fetch_messages)
    response = client.get("/emails?folder=INBOX&limit=1")
    assert response.status_code == 200
    data = response.json()
    assert data[0]["uid"] == "1"
