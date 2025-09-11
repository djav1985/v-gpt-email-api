import os
import sys
from pathlib import Path
import logging
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
from app import dependencies  # noqa: E402


def test_startup_with_signature(tmp_path):
    sig_file = Path("config/signature.txt")
    original = sig_file.read_text() if sig_file.exists() else None
    sig_file.write_text("Hello")
    with TestClient(app):
        pass
    assert dependencies.signature_text == "Hello"
    if original is not None:
        sig_file.write_text(original)
    else:
        sig_file.unlink()


def test_startup_without_signature(tmp_path):
    sig_file = Path("config/signature.txt")
    temp = Path("config/signature.bak")
    if sig_file.exists():
        sig_file.rename(temp)
    with TestClient(app):
        pass
    assert dependencies.signature_text == ""
    if temp.exists():
        temp.rename(sig_file)


def test_startup_does_not_configure_logging(monkeypatch):
    original_level = logging.getLogger().level
    called = False

    def fake_basicConfig(*args, **kwargs):
        nonlocal called
        called = True

    monkeypatch.setattr(logging, "basicConfig", fake_basicConfig)
    with TestClient(app):
        pass
    assert not called
    assert logging.getLogger().level == original_level


def test_startup_missing_env(monkeypatch):
    monkeypatch.delenv("ACCOUNT_EMAIL", raising=False)
    with pytest.raises(RuntimeError):
        with TestClient(app):
            pass
