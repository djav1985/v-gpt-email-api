# models.py
from pydantic import BaseModel, Field, EmailStr
from typing import Optional

class SendEmailRequest(BaseModel):
    to_addresses: list[EmailStr] = Field(
        ...,
        description="List of recipient email addresses.",
    )
    subject: str = Field(..., description="The subject of the email.", max_length=255)
    body: str = Field(..., description="The body content of the email.")
    file_url: Optional[str] = Field(
        None,
        description="The URL or comma-separated URLs of the files to be downloaded and attached to the email.",
    )
