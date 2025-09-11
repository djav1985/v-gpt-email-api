# flake8: noqa
# models.py
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, HttpUrl, field_validator

class SendEmailRequest(BaseModel):
    to_addresses: list[EmailStr] = Field(
        ...,
        description="List of recipient email addresses.",
        min_items=1,
    )
    subject: str = Field(
        ...,
        description="The subject of the email.",
        max_length=255,
        min_length=1,
    )
    body: str = Field(
        ...,
        description="The body content of the email.",
        min_length=1,
    )
    file_url: Optional[list[HttpUrl]] = Field(
        None,
        description="The URL or comma-separated URLs of the files to be downloaded and attached to the email.",
    )

    @field_validator("file_url", mode="before")
    @classmethod
    def split_file_urls(cls, value: Optional[str | list[str]]) -> Optional[list[str]]:
        if value in (None, ""):
            return None
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            urls = [v.strip() for v in value.split(",") if v.strip()]
            return urls or None
        raise TypeError("file_url must be a string or list of URLs")


class EmailSummary(BaseModel):
    uid: str = Field(..., min_length=1)
    subject: str | None = None
    from_: str | None = Field(None, alias="from")
    date: datetime | None = None
    seen: bool

    class Config:
        allow_population_by_field_name = True
        json_encoders = {datetime: lambda v: v.isoformat()}


class MessageResponse(BaseModel):
    message: str = Field(..., min_length=1)
