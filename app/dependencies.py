# dependancies.py
import os
import aiosmtplib
import aiofiles
import aiohttp
import tempfile
import shutil
import mimetypes
import asyncio

from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

from typing import Optional


# Environment variables
ACCOUNT_EMAIL = os.getenv("ACCOUNT_EMAIL")
ACCOUNT_PASSWORD = os.getenv("ACCOUNT_PASSWORD")
ACCOUNT_SMTP_SERVER = os.getenv("ACCOUNT_SMTP_SERVER")
ACCOUNT_SMTP_PORT = os.getenv("ACCOUNT_SMTP_PORT")
ACCOUNT_REPLY_TO = os.getenv("ACCOUNT_REPLY_TO")
SIGNATURE_PATH = "/app/sig/signature.html"

# Validate environment variables
if not all([ACCOUNT_EMAIL, ACCOUNT_PASSWORD, ACCOUNT_SMTP_SERVER, ACCOUNT_SMTP_PORT]):
    raise HTTPException(status_code=500, detail="SMTP configuration is incomplete")

ACCOUNT_SMTP_PORT = int(ACCOUNT_SMTP_PORT)

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
    to_address: str,
    subject: str,
    body: str,
    file_url: Optional[str] = None,
) -> None:
    if not os.path.exists(SIGNATURE_PATH) or not os.access(SIGNATURE_PATH, os.R_OK):
        raise HTTPException(status_code=500, detail="Signature file not found or is not readable")

    msg = MIMEMultipart()
    # Convert to_address string into a list of email addresses
    to_addresses = [address.strip() for address in to_address.split(",")]
    msg["From"] = ACCOUNT_EMAIL
    msg["To"] = ", ".join(to_addresses)
    msg["Subject"] = subject
    msg["Reply-To"] = ACCOUNT_REPLY_TO

    # Add the email body and signature
    async with aiofiles.open(SIGNATURE_PATH, "r") as file:
        signature = await file.read()
    msg.attach(MIMEText(body + signature, "html"))

    # Handle file attachments
    if file_url:
        # Convert the file_url string into a list of URLs
        file_urls = [url.strip() for url in file_url.split(",")]

        total_size = 0
        temp_dir = tempfile.mkdtemp()

        try:
            async with aiohttp.ClientSession() as session:
                # Download all files concurrently
                file_paths = await asyncio.gather(
                    *(fetch_file(session, url, temp_dir) for url in file_urls)
                )

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

                    with open(file_path, "rb") as file:
                        part.set_payload(file.read())

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
            hostname=ACCOUNT_SMTP_SERVER,
            port=ACCOUNT_SMTP_PORT,
            username=ACCOUNT_EMAIL,
            password=ACCOUNT_PASSWORD,
            start_tls=True,
        )
    except aiosmtplib.errors.SMTPException as e:
        print(f"SMTPException: {str(e)}")
        raise HTTPException(status_code=500, detail=f"SMTP server error: {str(e)}")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


async def get_api_key(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
) -> Optional[str]:
    # Retrieve the API key from the environment
    expected_key = os.getenv("API_KEY")

    # If API_KEY is set in the environment, enforce validation
    if expected_key:
        if not credentials or credentials.credentials != expected_key:
            raise HTTPException(status_code=403, detail="Invalid or missing API key")

    # If API_KEY is not set, allow access without validation
    return credentials.credentials if credentials else None
