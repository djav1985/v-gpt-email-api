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
from app import dependencies

dependencies.settings = dependencies.Config()
client = TestClient(app)


def test_send_email(monkeypatch):
    async def mock_send_email(to_addresses, subject, body, file_url, headers=None):
        return None

    monkeypatch.setattr("app.routes.send_email.send_email", mock_send_email)
    response = client.post(
        "/",
        json={"to_addresses": ["a@b.com"], "subject": "Sub", "body": "Body", "file_url": None},
    )
    assert response.status_code == 201
    assert response.json() == {"message": "Email sent successfully"}
