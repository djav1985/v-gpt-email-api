# flake8: noqa
import os
import sys
from fastapi.testclient import TestClient
from fastapi import HTTPException

os.environ["ACCOUNT_EMAIL"] = "user@example.com"
os.environ["ACCOUNT_PASSWORD"] = "password"
os.environ["ACCOUNT_SMTP_SERVER"] = "smtp.example.com"
os.environ["ACCOUNT_SMTP_PORT"] = "587"
os.environ["ACCOUNT_IMAP_SERVER"] = "imap.example.com"
os.environ["ACCOUNT_IMAP_PORT"] = "993"

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app  # noqa: E402
from app import dependencies

dependencies.settings = dependencies.Config()
client = TestClient(app)


def test_send_email(monkeypatch):
    captured = {}

    async def mock_send_email(to_addresses, subject, body, file_urls, headers=None):
        captured["file_urls"] = file_urls
        return None

    monkeypatch.setattr("app.routes.send_email.send_email", mock_send_email)
    urls = ["http://f1.txt/", "http://f2.txt/"]
    response = client.post(
        "/",
        json={
            "to_addresses": ["a@b.com"],
            "subject": "Sub",
            "body": "Body",
            "file_url": urls,
        },
    )
    assert response.status_code == 201
    assert response.json() == {"message": "Email sent successfully"}
    assert captured["file_urls"] == urls

def test_send_email_http_error(monkeypatch):
    async def mock_send(*a, **k):
        raise HTTPException(status_code=400, detail="bad")
    monkeypatch.setattr("app.routes.send_email.send_email", mock_send)
    resp = client.post(
        "/",
        json={"to_addresses": ["a@b.com"], "subject": "S", "body": "B", "file_url": None},
    )
    assert resp.status_code == 400


def test_send_email_generic_error(monkeypatch):
    async def mock_send(*a, **k):
        raise RuntimeError("boom")
    monkeypatch.setattr("app.routes.send_email.send_email", mock_send)
    resp = client.post(
        "/",
        json={"to_addresses": ["a@b.com"], "subject": "S", "body": "B", "file_url": None},
    )
    assert resp.status_code == 500


def test_send_email_missing_settings(monkeypatch):
    monkeypatch.setattr(dependencies, "settings", None)
    resp = client.post(
        "/",
        json={"to_addresses": ["a@b.com"], "subject": "S", "body": "B", "file_url": None},
    )
    assert resp.status_code == 500
