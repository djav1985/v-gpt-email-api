# flake8: noqa
import os
import sys
import asyncio
import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

os.environ["ACCOUNT_EMAIL"] = "user@example.com"
os.environ["ACCOUNT_PASSWORD"] = "password"
os.environ["ACCOUNT_SMTP_SERVER"] = "smtp.example.com"
os.environ["ACCOUNT_SMTP_PORT"] = "587"
os.environ["ACCOUNT_IMAP_SERVER"] = "imap.example.com"
os.environ["ACCOUNT_IMAP_PORT"] = "993"

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import dependencies


class DummySession:
    pass


def test_fetch_file_invalid_scheme(tmp_path):
    with pytest.raises(HTTPException):
        asyncio.run(dependencies.fetch_file(DummySession(), "ftp://example.com/file.txt", tmp_path))


def test_send_email_without_settings():
    original = dependencies.settings
    dependencies.settings = None
    with pytest.raises(RuntimeError):
        asyncio.run(
            dependencies.send_email(
                ["a@example.com"],
                "Subject",
                "Body",
            )
        )
    dependencies.settings = original


def test_get_api_key_without_env(monkeypatch):
    monkeypatch.delenv("API_KEY", raising=False)
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="token")
    assert (
        asyncio.run(dependencies.get_api_key(credentials=creds))
        == "token"
    )
    assert asyncio.run(dependencies.get_api_key(credentials=None)) is None


def test_get_api_key_with_env_valid(monkeypatch):
    monkeypatch.setenv("API_KEY", "secret")
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="secret")
    assert (
        asyncio.run(dependencies.get_api_key(credentials=creds))
        == "secret"
    )


def test_get_api_key_with_env_invalid(monkeypatch):
    monkeypatch.setenv("API_KEY", "secret")
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="wrong")
    with pytest.raises(HTTPException):
        asyncio.run(dependencies.get_api_key(credentials=creds))
    with pytest.raises(HTTPException):
        asyncio.run(dependencies.get_api_key(credentials=None))
