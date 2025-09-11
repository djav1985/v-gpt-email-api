import pytest
import pytest_asyncio
from httpx import AsyncClient
from asgi_lifespan import LifespanManager

from app.main import app


@pytest.fixture(autouse=True)
def env(monkeypatch):
    monkeypatch.setenv("ACCOUNT_EMAIL", "user@example.com")
    monkeypatch.setenv("ACCOUNT_PASSWORD", "password")
    monkeypatch.setenv("ACCOUNT_SMTP_SERVER", "smtp.example.com")
    monkeypatch.setenv("ACCOUNT_SMTP_PORT", "587")
    monkeypatch.setenv("ACCOUNT_IMAP_SERVER", "imap.example.com")
    monkeypatch.setenv("ACCOUNT_IMAP_PORT", "993")


@pytest_asyncio.fixture
async def client(env):
    async with LifespanManager(app):
        async with AsyncClient(app=app, base_url="http://test") as ac:
            ac.headers["Authorization"] = "Bearer token"
            yield ac
