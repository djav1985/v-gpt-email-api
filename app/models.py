# models.py
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List

class SendEmailRequest(BaseModel):
    to_address: List[EmailStr] = Field(
        ...,
        description="The recipient email addresses.",
    )
    subject: str = Field(..., description="The subject of the email.", max_length=255)
    body: str = Field(..., description="The body content of the email.")
    file_url: Optional[str] = Field(
        None,
        description="The URL or comma-separated URLs of the files to be downloaded and attached to the email.",
    )
