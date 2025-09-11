# flake8: noqa
import os
import sys
import asyncio
import pytest
from fastapi import HTTPException

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
