import os
import aiosmtplib
import aiofiles
import aiohttp
import tempfile
import shutil
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from typing import Union, List, Optional
from pydantic import EmailStr
from fastapi import HTTPException, Depends

ACCOUNT_EMAIL = os.getenv("ACCOUNT_EMAIL")
ACCOUNT_PASSWORD = os.getenv("ACCOUNT_PASSWORD")
ACCOUNT_SMTP_SERVER = os.getenv("ACCOUNT_SMTP_SERVER")
ACCOUNT_SMTP_PORT = int(os.getenv("ACCOUNT_SMTP_PORT"))
ACCOUNT_REPLY_TO = os.getenv("ACCOUNT_REPLY_TO")
SIGNATURE_PATH = "/app/sig/signature.html"

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


async def fetch_file(session, url, temp_dir):
    async with session.get(url) as response:
        if response.status != 200:
            raise HTTPException(
                status_code=response.status,
                detail=f"Failed to download file from {url}",
            )

        filename = url.split("/")[-1]
        file_path = os.path.join(temp_dir, filename)

        async with aiofiles.open(file_path, "wb") as out_file:
            content = await response.read()
            await out_file.write(content)

        return file_path


async def send_email(
    to_address: Union[EmailStr, List[EmailStr]],
    subject: str,
    body: str,
    file_url: Optional[Union[str, List[str]]] = None,
):
    if not os.path.exists(SIGNATURE_PATH):
        raise HTTPException(status_code=500, detail="Signature file not found")

    msg = MIMEMultipart()
    msg["From"] = ACCOUNT_EMAIL
    msg["To"] = ", ".join(to_address) if isinstance(to_address, list) else to_address
    msg["Subject"] = subject
    msg["Reply-To"] = ACCOUNT_REPLY_TO

    # Add the email body and signature
    async with aiofiles.open(SIGNATURE_PATH, "r") as file:
        signature = await file.read()
    msg.attach(MIMEText(body + signature, "html"))

    # Handle file attachments
    if file_url:
        if isinstance(file_url, str):
            file_url = [file_url]

        total_size = 0
        temp_dir = tempfile.mkdtemp()

        try:
            async with aiohttp.ClientSession() as session:
                for url in file_url:
                    file_path = await fetch_file(session, url, temp_dir)
                    file_size = os.path.getsize(file_path)

                    if file_size + total_size > MAX_ATTACHMENT_SIZE:
                        raise HTTPException(
                            status_code=413,
                            detail="Total attachment size exceeds 20MB limit",
                        )

                    total_size += file_size
                    part = MIMEBase("application", "octet-stream")
                    with open(file_path, "rb") as file:
                        part.set_payload(file.read())

                    encoders.encode_base64(part)
                    part.add_header(
                        "Content-Disposition",
                        f"attachment; filename={os.path.basename(file_path)}",
                    )
                    msg.attach(part)
        finally:
            shutil.rmtree(temp_dir)

    await aiosmtplib.send(
        msg,
        hostname=ACCOUNT_SMTP_SERVER,
        port=ACCOUNT_SMTP_PORT,
        username=ACCOUNT_EMAIL,
        password=ACCOUNT_PASSWORD,
        use_tls=True,
    )


# This function checks if the provided API key is valid or not
async def get_api_key(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False)),
):
    if os.getenv("MEMORIES_API_KEY") and (
        not credentials or credentials.credentials != os.getenv("MEMORIES_API_KEY")
    ):
        raise HTTPException(status_code=403, detail="Invalid or missing API key")
    return credentials.credentials if credentials else None
