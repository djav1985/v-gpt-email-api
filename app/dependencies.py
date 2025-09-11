# flake8: noqa
# dependancies.py
import os
import aiosmtplib
import aiofiles
import aiohttp
import tempfile
import shutil
import mimetypes
import asyncio
from urllib.parse import urlparse

from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

from typing import Optional

from pydantic import EmailStr, Field
from pydantic_settings import BaseSettings


api_key_scheme = HTTPBearer(
    auto_error=False,
    scheme_name="APIKey",
    description="Supply the API key as a Bearer token in the Authorization header.",
)


class Config(BaseSettings):
    """Application configuration loaded from environment variables."""

    account_email: EmailStr = Field(env="ACCOUNT_EMAIL")
    account_password: str = Field(env="ACCOUNT_PASSWORD")
    account_smtp_server: str = Field(env="ACCOUNT_SMTP_SERVER")
    account_smtp_port: int = Field(env="ACCOUNT_SMTP_PORT")
    account_imap_server: str = Field(env="ACCOUNT_IMAP_SERVER")
    account_imap_port: int = Field(env="ACCOUNT_IMAP_PORT")
    from_name: str = Field(default="", env="FROM_NAME")
    attachment_concurrency: int = Field(default=3, env="ATTACHMENT_CONCURRENCY")
    start_tls: bool = Field(default=True, env="START_TLS")
    account_reply_to: EmailStr | None = Field(default=None, env="ACCOUNT_REPLY_TO")


settings: Config | None = None
signature_text: str = ""

ALLOWED_FILE_TYPES = {
    ".zip",
    ".txt",
    ".docx",
    ".png",
    ".webp",
    ".jpg",
    ".jpeg",
    ".pdf",
    ".rtf",
}
MAX_ATTACHMENT_SIZE = 20 * 1024 * 1024  # 20MB


async def fetch_file(session, url, temp_dir) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise HTTPException(status_code=400, detail="Invalid URL scheme")

    filename = url.split("/")[-1]
    _, file_extension = os.path.splitext(filename)

    # Check if the file type is allowed
    if file_extension.lower() not in ALLOWED_FILE_TYPES:
        raise HTTPException(status_code=400, detail=f"File type {file_extension} is not allowed")

    # Set timeout for requests
    timeout = aiohttp.ClientTimeout(total=10)
    async with session.get(url, timeout=timeout) as response:
        if response.status != 200:
            print(f"Failed to download file from {url} with status {response.status}")
            raise HTTPException(
                status_code=response.status,
                detail=f"Failed to download file from {url}",
            )

        file_path = os.path.join(temp_dir, filename)

        async with aiofiles.open(file_path, "wb") as out_file:
            content = await response.read()
            await out_file.write(content)

        return file_path

async def send_email(
    to_addresses: list[EmailStr],
    subject: str,
    body: str,
    file_url: Optional[str] = None,
    headers: Optional[dict[str, str]] = None,
) -> None:
    if settings is None:
        raise RuntimeError("Settings have not been initialized")

    msg = MIMEMultipart()
    msg["From"] = f"{settings.from_name} <{settings.account_email}>"
    msg["To"] = ", ".join(to_addresses)
    msg["Subject"] = subject
    if settings.account_reply_to is not None:
        msg["Reply-To"] = settings.account_reply_to

    msg.attach(MIMEText(body + signature_text, "html"))

    if headers:
        for key, value in headers.items():
            msg[key] = value

    # Handle file attachments
    if file_url:
        file_urls = [url.strip() for url in file_url.split(",")]

        total_size = 0
        temp_dir = tempfile.mkdtemp()
        semaphore = asyncio.Semaphore(settings.attachment_concurrency)
        connector = aiohttp.TCPConnector(limit=settings.attachment_concurrency)

        async def sem_fetch(url: str) -> str:
            async with semaphore:
                return await fetch_file(session, url, temp_dir)

        try:
            async with aiohttp.ClientSession(connector=connector) as session:
                file_paths = await asyncio.gather(*(sem_fetch(url) for url in file_urls))

                for file_path in file_paths:
                    file_size = os.path.getsize(file_path)

                    if file_size + total_size > MAX_ATTACHMENT_SIZE:
                        raise HTTPException(
                            status_code=413,
                            detail="Total attachment size exceeds 20MB limit",
                        )

                    if file_size > MAX_ATTACHMENT_SIZE:
                        raise HTTPException(
                            status_code=413,
                            detail=f"Attachment {os.path.basename(file_path)} exceeds the 20MB limit",
                        )

                    total_size += file_size
                    mime_type, _ = mimetypes.guess_type(file_path)
                    main_type, sub_type = (
                        mime_type.split("/") if mime_type else ("application", "octet-stream")
                    )
                    part = MIMEBase(main_type, sub_type)

                    async with aiofiles.open(file_path, "rb") as file:
                        file_data = await file.read()
                    part.set_payload(file_data)

                    encoders.encode_base64(part)
                    part.add_header(
                        "Content-Disposition",
                        f"attachment; filename={os.path.basename(file_path)}",
                    )
                    msg.attach(part)
        except HTTPException as e:
            print(f"HTTPException during file handling: {e.detail}")
            raise
        except Exception as e:
            print(f"Unexpected error during file handling: {str(e)}")
            raise
        finally:
            shutil.rmtree(temp_dir)

    try:
        await aiosmtplib.send(
            msg,
            hostname=settings.account_smtp_server,
            port=settings.account_smtp_port,
            username=settings.account_email,
            password=settings.account_password,
            start_tls=settings.start_tls,
        )
    except aiosmtplib.errors.SMTPException as e:
        print(f"SMTPException: {str(e)}")
        raise HTTPException(status_code=500, detail=f"SMTP server error: {str(e)}")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

async def get_api_key(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(api_key_scheme),
) -> Optional[str]:
    # Retrieve the API key from the environment
    expected_key = os.getenv("API_KEY")

    # If API_KEY is set in the environment, enforce validation
    if expected_key:
        if not credentials or credentials.credentials != expected_key:
            raise HTTPException(status_code=403, detail="Invalid or missing API key")

    # If API_KEY is not set, allow access without validation
    return credentials.credentials if credentials else None
