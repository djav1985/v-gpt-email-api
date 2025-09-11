from email.message import EmailMessage
import imaplib
import pytest


@pytest.mark.asyncio
async def test_list_folders(monkeypatch, client):
    class DummyIMAP:
        def login(self, *args, **kwargs):
            pass

        def list(self):
            return "OK", [
                b'(\\HasNoChildren) "/" "INBOX"',
                b'(\\HasNoChildren) "/" "Archive"',
            ]

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    monkeypatch.setattr(imaplib, "IMAP4_SSL", lambda *a, **k: DummyIMAP())
    response = await client.get("/imap/folders")
    assert response.status_code == 200
    assert response.json() == {"folders": ["INBOX", "Archive"]}


@pytest.mark.asyncio
async def test_fetch_messages(monkeypatch, client):
    class DummyIMAP:
        def login(self, *args, **kwargs):
            pass

        def select(self, folder):
            pass

        def search(self, charset, criteria):
            return "OK", [b"1"]

        def uid(self, cmd, uid, spec):
            if cmd == "fetch":
                msg = EmailMessage()
                msg["Subject"] = "=?utf-8?B?VGVzdA==?="
                msg["From"] = "test@example.com"
                msg["Date"] = "Mon, 02 Oct 2023 13:00:00 +0000"
                return "OK", [(b"1 (FLAGS (\\Seen))", bytes(msg))]
            return "NO", []

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    monkeypatch.setattr(imaplib, "IMAP4_SSL", lambda *a, **k: DummyIMAP())
    response = await client.get("/imap/emails")
    assert response.status_code == 200
    data = response.json()
    assert data[0]["subject"] == "Test"


@pytest.mark.asyncio
async def test_fetch_message(monkeypatch, client):
    class DummyIMAP:
        def login(self, *args, **kwargs):
            pass

        def select(self, folder):
            pass

        def uid(self, cmd, uid, spec):
            if cmd == "fetch":
                msg = EmailMessage()
                msg.set_content("hi")
                return "OK", [(None, msg.as_bytes())]
            return "NO", []

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    monkeypatch.setattr(imaplib, "IMAP4_SSL", lambda *a, **k: DummyIMAP())
    response = await client.get("/imap/emails/1")
    assert response.status_code == 200
    assert response.json()["body"].strip() == "hi"
