import logging
from pathlib import Path

import pytest
from httpx import AsyncClient
from asgi_lifespan import LifespanManager

from app.main import app
from app import dependencies


@pytest.mark.asyncio
async def test_startup_with_signature(tmp_path):
    sig_file = Path("config/signature.txt")
    original = sig_file.read_text() if sig_file.exists() else None
    sig_file.write_text("Hello")
    async with LifespanManager(app):
        async with AsyncClient(app=app, base_url="http://test") as client:
            client.headers["X-API-Key"] = "token"
            await client.get("/openapi.json")
    assert dependencies.signature_text == "Hello"
    if original is not None:
        sig_file.write_text(original)
    else:
        sig_file.unlink()


@pytest.mark.asyncio
async def test_startup_without_signature(tmp_path):
    sig_file = Path("config/signature.txt")
    temp = Path("config/signature.bak")
    if sig_file.exists():
        sig_file.rename(temp)
    dependencies.signature_text = ""
    async with LifespanManager(app):
        async with AsyncClient(app=app, base_url="http://test") as client:
            client.headers["X-API-Key"] = "token"
            await client.get("/openapi.json")
    assert dependencies.signature_text == ""
    if temp.exists():
        temp.rename(sig_file)


@pytest.mark.asyncio
async def test_startup_does_not_configure_logging(monkeypatch):
    original_level = logging.getLogger().level
    called = False

    def fake_basicConfig(*args, **kwargs):
        nonlocal called
        called = True

    monkeypatch.setattr(logging, "basicConfig", fake_basicConfig)
    async with LifespanManager(app):
        async with AsyncClient(app=app, base_url="http://test") as client:
            client.headers["X-API-Key"] = "token"
            await client.get("/openapi.json")
    assert not called
    assert logging.getLogger().level == original_level


@pytest.mark.asyncio
async def test_startup_missing_env(monkeypatch):
    monkeypatch.delenv("ACCOUNT_EMAIL", raising=False)
    with pytest.raises(RuntimeError):
        async with LifespanManager(app):
            pass
