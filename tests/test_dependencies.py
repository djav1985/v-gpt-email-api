# flake8: noqa
import asyncio
import os
import sys
from pathlib import Path

import aiofiles
import aiosmtplib
import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

# Set required environment variables
os.environ["ACCOUNT_EMAIL"] = "user@example.com"
os.environ["ACCOUNT_PASSWORD"] = "password"
os.environ["ACCOUNT_SMTP_SERVER"] = "smtp.example.com"
os.environ["ACCOUNT_SMTP_PORT"] = "587"
os.environ["ACCOUNT_IMAP_SERVER"] = "imap.example.com"
os.environ["ACCOUNT_IMAP_PORT"] = "993"

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import dependencies  # noqa: E402


@pytest.fixture(autouse=True)
def setup_settings():
    dependencies.settings = dependencies.Config()
    yield
    dependencies.settings = None


class MockResponse:
    def __init__(self, status: int, data: bytes = b"content"):
        self.status = status
        self._data = data

    async def read(self) -> bytes:
        return self._data

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass


class MockSession:
    def __init__(self, response: MockResponse):
        self._response = response

    def get(self, url, timeout):
        return self._response


def test_fetch_file_success(tmp_path):
    session = MockSession(MockResponse(200, b"data"))
    file_path = asyncio.run(
        dependencies.fetch_file(session, "http://example.com/file.txt", tmp_path)
    )
    assert Path(file_path).exists()


def test_fetch_file_non_200(tmp_path):
    session = MockSession(MockResponse(404))
    with pytest.raises(HTTPException) as exc:
        asyncio.run(
            dependencies.fetch_file(session, "http://example.com/file.txt", tmp_path)
        )
    assert exc.value.status_code == 404


def test_fetch_file_disallowed_extension(tmp_path):
    session = MockSession(MockResponse(200))
    with pytest.raises(HTTPException):
        asyncio.run(
            dependencies.fetch_file(session, "http://example.com/file.exe", tmp_path)
        )


async def fake_fetch_file(session, url, temp_dir):
    path = Path(temp_dir) / Path(url).name
    async with aiofiles.open(path, "wb") as f:
        await f.write(b"x")
    return str(path)


def test_send_email_with_attachment(monkeypatch):
    monkeypatch.setattr(dependencies, "fetch_file", fake_fetch_file)
    sent = {}

    async def mock_send(msg, **kwargs):
        sent["msg"] = msg

    monkeypatch.setattr(aiosmtplib, "send", mock_send)
    dependencies.settings.account_reply_to = "reply@example.com"
    asyncio.run(dependencies.send_email(["a@b.com"], "Sub", "Body", "http://f1.txt"))
    assert "Reply-To" in sent["msg"]


def test_send_email_total_size_exceeded(monkeypatch):
    async def fake_fetch(session, url, temp_dir):
        path = Path(temp_dir) / Path(url).name
        async with aiofiles.open(path, "wb") as f:
            await f.write(b"x")
        return str(path)

    monkeypatch.setattr(dependencies, "fetch_file", fake_fetch)
    sizes = [15 * 1024 * 1024, 10 * 1024 * 1024]
    monkeypatch.setattr("app.dependencies.os.path.getsize", lambda _: sizes.pop(0))
    with pytest.raises(HTTPException) as exc:
        asyncio.run(
            dependencies.send_email(
                ["a@b.com"], "Sub", "Body", "http://f1.txt,http://f2.txt"
            )
        )
    assert exc.value.status_code == 413


def test_send_email_single_file_oversize(monkeypatch):
    monkeypatch.setattr(dependencies, "fetch_file", fake_fetch_file)
    monkeypatch.setattr("app.dependencies.os.path.getsize", lambda _: 25 * 1024 * 1024)
    with pytest.raises(HTTPException) as exc:
        asyncio.run(
            dependencies.send_email(["a@b.com"], "Sub", "Body", "http://f1.txt")
        )
    assert exc.value.status_code == 413


def test_send_email_missing_reply_to(monkeypatch):
    dependencies.settings.account_reply_to = None
    sent = {}

    async def mock_send(msg, **kwargs):
        sent["msg"] = msg

    monkeypatch.setattr(aiosmtplib, "send", mock_send)
    asyncio.run(dependencies.send_email(["a@b.com"], "Sub", "Body"))
    assert "Reply-To" not in sent["msg"]


def test_send_email_smtp_exception(monkeypatch):
    async def mock_send(*args, **kwargs):
        raise aiosmtplib.errors.SMTPException("fail")

    monkeypatch.setattr(aiosmtplib, "send", mock_send)
    with pytest.raises(HTTPException) as exc:
        asyncio.run(dependencies.send_email(["a@b.com"], "Sub", "Body"))
    assert exc.value.status_code == 500


# Existing API key tests retained

def test_get_api_key_without_env(monkeypatch):
    monkeypatch.delenv("API_KEY", raising=False)
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="token")
    assert asyncio.run(dependencies.get_api_key(credentials=creds)) == "token"
    assert asyncio.run(dependencies.get_api_key(credentials=None)) is None


def test_get_api_key_with_env_valid(monkeypatch):
    monkeypatch.setenv("API_KEY", "secret")
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="secret")
    assert asyncio.run(dependencies.get_api_key(credentials=creds)) == "secret"


def test_get_api_key_with_env_invalid(monkeypatch):
    monkeypatch.setenv("API_KEY", "secret")
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="wrong")
    with pytest.raises(HTTPException):
        asyncio.run(dependencies.get_api_key(credentials=creds))
    with pytest.raises(HTTPException):
        asyncio.run(dependencies.get_api_key(credentials=None))
