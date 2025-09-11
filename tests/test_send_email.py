import pytest
from fastapi import HTTPException

from app import dependencies


@pytest.mark.asyncio
async def test_send_email(monkeypatch, client):
    captured = {}

    async def mock_send_email(to_addresses, subject, body, file_urls, headers=None):
        captured["file_urls"] = file_urls
        return None

    monkeypatch.setattr("app.routes.send_email.send_email", mock_send_email)
    urls = ["http://f1.txt/", "http://f2.txt/"]
    response = await client.post(
        "/",
        json={
            "to_addresses": ["a@b.com"],
            "subject": "Sub",
            "body": "Body",
            "file_urls": urls,
        },
        follow_redirects=True,
    )
    assert response.status_code == 201
    assert response.json() == {"message": "Email sent successfully"}
    assert captured["file_urls"] == urls


@pytest.mark.asyncio
async def test_send_email_http_error(monkeypatch, client):
    async def mock_send(*a, **k):
        raise HTTPException(status_code=400, detail="bad")

    monkeypatch.setattr("app.routes.send_email.send_email", mock_send)
    resp = await client.post(
        "/",
        json={
            "to_addresses": ["a@b.com"],
            "subject": "S",
            "body": "B",
            "file_urls": None,
        },
        follow_redirects=True,
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_send_email_generic_error(monkeypatch, client):
    async def mock_send(*a, **k):
        raise RuntimeError("boom")

    monkeypatch.setattr("app.routes.send_email.send_email", mock_send)
    resp = await client.post(
        "/",
        json={
            "to_addresses": ["a@b.com"],
            "subject": "S",
            "body": "B",
            "file_urls": None,
        },
        follow_redirects=True,
    )
    assert resp.status_code == 500


@pytest.mark.asyncio
async def test_send_email_missing_settings(monkeypatch, client):
    monkeypatch.setattr(dependencies, "settings", None)
    resp = await client.post(
        "/",
        json={
            "to_addresses": ["a@b.com"],
            "subject": "S",
            "body": "B",
            "file_urls": None,
        },
        follow_redirects=True,
    )
    assert resp.status_code == 500


@pytest.mark.asyncio
async def test_send_email_missing_api_key(client):
    del client.headers["X-API-Key"]
    resp = await client.post(
        "/",
        json={
            "to_addresses": ["a@b.com"],
            "subject": "S",
            "body": "B",
            "file_urls": None,
        },
        follow_redirects=True,
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_send_email_invalid_api_key(monkeypatch, client):
    dependencies.settings.api_key = "expected"
    client.headers["X-API-Key"] = "wrong"
    resp = await client.post(
        "/",
        json={
            "to_addresses": ["a@b.com"],
            "subject": "S",
            "body": "B",
            "file_urls": None,
        },
        follow_redirects=True,
    )
    assert resp.status_code == 401
    dependencies.settings.api_key = None
    client.headers["X-API-Key"] = "token"
