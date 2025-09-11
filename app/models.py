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


class EmailSummary(BaseModel):
    uid: str
    subject: str | None = None
    from_: str | None = Field(None, alias="from")
    date: str | None = None
    seen: bool

    class Config:
        allow_population_by_field_name = True
