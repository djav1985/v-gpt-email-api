# flake8: noqa
from datetime import datetime
import os
import sys

import pytest
from pydantic import ValidationError

os.environ["ACCOUNT_EMAIL"] = "user@example.com"
os.environ["ACCOUNT_PASSWORD"] = "password"
os.environ["ACCOUNT_SMTP_SERVER"] = "smtp.example.com"
os.environ["ACCOUNT_SMTP_PORT"] = "587"
os.environ["ACCOUNT_IMAP_SERVER"] = "imap.example.com"
os.environ["ACCOUNT_IMAP_PORT"] = "993"

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.models import SendEmailRequest, EmailSummary  # noqa: E402


def test_send_email_request_invalid_email():
    with pytest.raises(ValidationError):
        SendEmailRequest(to_addresses=["not-an-email"], subject="S", body="B")


def test_send_email_request_long_subject():
    with pytest.raises(ValidationError):
        SendEmailRequest(to_addresses=["a@b.com"], subject="a" * 256, body="B")


def test_email_summary_alias_and_datetime():
    dt = datetime(2024, 1, 1, 12, 0, 0)
    summary = EmailSummary(uid="1", subject="S", **{"from": "a@b.com"}, date=dt, seen=True)
    data = summary.model_dump(by_alias=True)
    assert data["from"] == "a@b.com"
    json_data = summary.model_dump_json(by_alias=True)
    assert dt.isoformat() in json_data
