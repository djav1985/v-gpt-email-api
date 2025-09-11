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
        example=["friend@example.com"],
    )
    subject: str = Field(
        ...,
        description="The subject of the email.",
        max_length=255,
        min_length=1,
        example="Hello",
    )
    body: str = Field(
        ...,
        description="The body content of the email.",
        min_length=1,
        example="Hi there",
    )
    file_url: Optional[list[HttpUrl]] = Field(
        None,
        description="The URL or comma-separated URLs of the files to be downloaded and attached to the email.",
        example=["https://example.com/file.txt"],
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
    uid: str = Field(
        ...,
        min_length=1,
        description="Unique identifier of the email.",
        example="1",
    )
    subject: str | None = Field(
        None,
        max_length=255,
        description="Subject line of the email.",
        example="Hello",
    )
    from_: str | None = Field(
        None,
        alias="from",
        max_length=255,
        description="Sender email address.",
        example="sender@example.com",
    )
    date: datetime | None = Field(
        None,
        description="Date the email was sent.",
        example="2024-01-01T12:00:00Z",
    )
    seen: bool = Field(
        ...,
        description="Whether the email has been read.",
        example=False,
    )

    class Config:
        allow_population_by_field_name = True
        json_encoders = {datetime: lambda v: v.isoformat()}


class MessageResponse(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        description="Human-readable response message.",
        example="Email sent",
    )


class ErrorResponse(BaseModel):
    detail: str = Field(
        ...,
        min_length=1,
        description="Error message detail.",
        example="Invalid request",
    )
    code: str | None = Field(
        None,
        description="Optional error code.",
        example="invalid_request",
    )
