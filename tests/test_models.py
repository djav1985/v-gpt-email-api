from datetime import datetime

import pytest
from pydantic import ValidationError

from app.models import EmailSummary, ErrorResponse, MessageResponse, SendEmailRequest


@pytest.mark.asyncio
async def test_send_email_request_invalid_email():
    with pytest.raises(ValidationError):
        SendEmailRequest(to_addresses=["not-an-email"], subject="S", body="B")


@pytest.mark.asyncio
async def test_send_email_request_long_subject():
    with pytest.raises(ValidationError):
        SendEmailRequest(to_addresses=["a@b.com"], subject="a" * 256, body="B")


@pytest.mark.asyncio
async def test_send_email_request_empty_fields():
    with pytest.raises(ValidationError):
        SendEmailRequest(to_addresses=[], subject="S", body="B")
    with pytest.raises(ValidationError):
        SendEmailRequest(to_addresses=["a@b.com"], subject="", body="B")
    with pytest.raises(ValidationError):
        SendEmailRequest(to_addresses=["a@b.com"], subject="S", body="")


@pytest.mark.asyncio
async def test_send_email_request_invalid_attachment_urls():
    with pytest.raises(ValidationError):
        SendEmailRequest(
            to_addresses=["a@b.com"],
            subject="S",
            body="B",
            file_urls="https://example.com,not-a-url",
        )


@pytest.mark.asyncio
async def test_email_summary_alias_and_datetime():
    dt = datetime(2024, 1, 1, 12, 0, 0)
    summary = EmailSummary(
        uid="1", subject="S", **{"from": "a@b.com"}, date=dt, seen=True
    )
    data = summary.model_dump(by_alias=True)
    assert data["from"] == "a@b.com"
    json_data = summary.model_dump_json(by_alias=True)
    assert dt.isoformat() in json_data


@pytest.mark.asyncio
async def test_email_summary_invalid_uid():
    with pytest.raises(ValidationError):
        EmailSummary(uid="", seen=True)
    with pytest.raises(ValidationError):
        EmailSummary(uid=None, seen=True)  # type: ignore


@pytest.mark.asyncio
async def test_message_response_empty_message():
    with pytest.raises(ValidationError):
        MessageResponse(message="")


@pytest.mark.asyncio
async def test_error_response_optional_code():
    err = ErrorResponse(detail="Missing API key")
    assert err.detail == "Missing API key"
    assert err.code is None


@pytest.mark.asyncio
async def test_error_response_with_code():
    err = ErrorResponse(detail="Forbidden", code="forbidden")
    assert err.code == "forbidden"
