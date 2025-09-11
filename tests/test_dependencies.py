from pathlib import Path

import aiofiles
import aiosmtplib
import pytest
from fastapi import HTTPException

from app import dependencies


@pytest.fixture(autouse=True)
def setup_settings():
    dependencies.settings = dependencies.Config()
    yield
    dependencies.settings = None


class MockContent:
    def __init__(self, chunks: list[bytes]):
        self._chunks = chunks

    async def iter_chunked(self, size: int):
        for chunk in self._chunks:
            yield chunk


class MockResponse:
    def __init__(self, status: int, chunks: list[bytes] | None = None):
        self.status = status
        self.content = MockContent(chunks or [b"content"])

    async def read(self):  # pragma: no cover - should not be called
        raise AssertionError("read should not be called")

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass


class MockSession:
    def __init__(self, response: MockResponse):
        self._response = response

    def get(self, url, timeout):
        return self._response


@pytest.mark.asyncio
async def test_fetch_file_success(tmp_path):
    session = MockSession(MockResponse(200, [b"data"]))
    file_path = await dependencies.fetch_file(
        session, "http://example.com/file.txt", tmp_path
    )
    assert Path(file_path).exists()


@pytest.mark.asyncio
async def test_fetch_file_non_200(tmp_path):
    session = MockSession(MockResponse(404))
    with pytest.raises(HTTPException) as exc:
        await dependencies.fetch_file(session, "http://example.com/file.txt", tmp_path)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_fetch_file_disallowed_extension(tmp_path):
    session = MockSession(MockResponse(200))
    with pytest.raises(HTTPException):
        await dependencies.fetch_file(session, "http://example.com/file.exe", tmp_path)


@pytest.mark.asyncio
async def test_fetch_file_streams_chunks(tmp_path):
    chunks = [b"a" * 1024, b"b" * 1024, b"c" * 1024]
    session = MockSession(MockResponse(200, chunks))
    file_path = await dependencies.fetch_file(
        session, "http://example.com/file.txt", tmp_path
    )
    assert Path(file_path).stat().st_size == 3 * 1024


async def fake_fetch_file(session, url, temp_dir):
    path = Path(temp_dir) / Path(url).name
    async with aiofiles.open(path, "wb") as f:
        await f.write(b"x")
    return str(path)


@pytest.mark.asyncio
async def test_send_email_with_attachment(monkeypatch):
    monkeypatch.setattr(dependencies, "fetch_file", fake_fetch_file)
    sent = {}

    async def mock_send(msg, **kwargs):
        sent["msg"] = msg

    monkeypatch.setattr(aiosmtplib, "send", mock_send)
    dependencies.settings.account_reply_to = "reply@example.com"
    await dependencies.send_email(["a@b.com"], "Sub", "Body", ["http://f1.txt"])
    assert "Reply-To" in sent["msg"]


@pytest.mark.asyncio
async def test_send_email_with_multiple_attachments(monkeypatch):
    monkeypatch.setattr(dependencies, "fetch_file", fake_fetch_file)
    sent = {}

    async def mock_send(msg, **kwargs):
        sent["msg"] = msg

    monkeypatch.setattr(aiosmtplib, "send", mock_send)
    await dependencies.send_email(
        ["a@b.com"], "Sub", "Body", ["http://f1.txt", "http://f2.txt"]
    )
    # 1 body part + 2 attachments
    assert len(sent["msg"].get_payload()) == 3


@pytest.mark.asyncio
async def test_send_email_total_size_exceeded(monkeypatch):
    async def fake_fetch(session, url, temp_dir):
        path = Path(temp_dir) / Path(url).name
        async with aiofiles.open(path, "wb") as f:
            await f.write(b"x")
        return str(path)

    monkeypatch.setattr(dependencies, "fetch_file", fake_fetch)
    sizes = [15 * 1024 * 1024, 10 * 1024 * 1024]
    monkeypatch.setattr("app.dependencies.os.path.getsize", lambda _: sizes.pop(0))
    with pytest.raises(HTTPException) as exc:
        await dependencies.send_email(
            ["a@b.com"], "Sub", "Body", ["http://f1.txt", "http://f2.txt"]
        )
    assert exc.value.status_code == 413


@pytest.mark.asyncio
async def test_send_email_single_file_oversize(monkeypatch):
    monkeypatch.setattr(dependencies, "fetch_file", fake_fetch_file)
    monkeypatch.setattr("app.dependencies.os.path.getsize", lambda _: 25 * 1024 * 1024)
    with pytest.raises(HTTPException) as exc:
        await dependencies.send_email(["a@b.com"], "Sub", "Body", ["http://f1.txt"])
    assert exc.value.status_code == 413


@pytest.mark.asyncio
async def test_send_email_missing_reply_to(monkeypatch):
    dependencies.settings.account_reply_to = None
    sent = {}

    async def mock_send(msg, **kwargs):
        sent["msg"] = msg

    monkeypatch.setattr(aiosmtplib, "send", mock_send)
    await dependencies.send_email(["a@b.com"], "Sub", "Body")
    assert "Reply-To" not in sent["msg"]


@pytest.mark.asyncio
async def test_send_email_smtp_exception(monkeypatch):
    async def mock_send(*args, **kwargs):
        raise aiosmtplib.errors.SMTPException("fail")

    monkeypatch.setattr(aiosmtplib, "send", mock_send)
    with pytest.raises(HTTPException) as exc:
        await dependencies.send_email(["a@b.com"], "Sub", "Body")
    assert exc.value.status_code == 500


# Existing API key tests retained


@pytest.mark.asyncio
async def test_get_api_key_without_env(monkeypatch):
    dependencies.settings.api_key = None
    assert dependencies.get_api_key(api_key="token") == "token"
    with pytest.raises(HTTPException) as exc:
        dependencies.get_api_key(api_key=None)
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_get_api_key_with_env_valid(monkeypatch):
    dependencies.settings.api_key = "secret"
    assert dependencies.get_api_key(api_key="secret") == "secret"


@pytest.mark.asyncio
async def test_get_api_key_with_env_invalid(monkeypatch):
    dependencies.settings.api_key = "secret"
    with pytest.raises(HTTPException) as exc:
        dependencies.get_api_key(api_key="wrong")
    assert exc.value.status_code == 401
    with pytest.raises(HTTPException) as exc2:
        dependencies.get_api_key(api_key=None)
    assert exc2.value.status_code == 401
