"""Common data models and request/response schemas."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, HttpUrl, field_validator, ConfigDict


class ErrorResponse(BaseModel):
    """Standard error response format across all apps."""
    status: int = Field(..., description="HTTP status code of the error")
    code: str = Field(..., description="Application-specific error identifier") 
    message: str = Field(..., description="Human-readable summary of the error")
    details: Optional[str] = Field(
        None, description="Additional information that may help resolve the error"
    )

    model_config = ConfigDict(extra="forbid")


class SendEmailRequest(BaseModel):
    to_addresses: list[EmailStr] = Field(
        ...,
        description="List of recipient email addresses.",
        min_length=1,
        json_schema_extra={"example": ["friend@example.com"], "minItems": 1},
    )
    subject: str = Field(
        ...,
        description="The subject of the email.",
        max_length=255,
        min_length=1,
        json_schema_extra={"example": "Hello"},
    )
    body: str = Field(
        ...,
        description="The body content of the email.",
        min_length=1,
        json_schema_extra={"example": "Hi there"},
    )
    file_urls: Optional[list[HttpUrl]] = Field(
        default=None,
        description=(
            "The URL or comma-separated URLs of the files to be downloaded and "
            "attached to the email."
        ),
        json_schema_extra={"example": ["https://example.com/file.txt"]},
    )

    @field_validator("file_urls", mode="before")
    @classmethod
    def split_file_urls(cls, value: Optional[str | list[str]]) -> Optional[list[str]]:
        if value in (None, ""):
            return None
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            urls = [v.strip() for v in value.split(",") if v.strip()]
            return urls or None
        raise TypeError("file_urls must be a string or list of URLs")


class EmailSummary(BaseModel):
    uid: str = Field(
        ...,
        min_length=1,
        description="Unique identifier of the email.",
        json_schema_extra={"example": "1"},
    )
    subject: str | None = Field(
        default=None,
        max_length=255,
        description="Subject line of the email.",
        json_schema_extra={"example": "Hello"},
    )
    from_: EmailStr | None = Field(
        default=None,
        alias="from",
        max_length=255,
        description="Sender email address.",
        json_schema_extra={"example": "sender@example.com"},
    )
    date: datetime | None = Field(
        default=None,
        description="Date the email was sent.",
        json_schema_extra={"example": "2024-01-01T12:00:00Z"},
    )
    seen: bool = Field(
        ...,
        description="Whether the email has been read.",
        json_schema_extra={"example": False},
    )

    class Config:
        allow_population_by_field_name = True
        json_encoders = {datetime: lambda v: v.isoformat()}


class MessageResponse(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        description="Human-readable response message.",
        json_schema_extra={"example": "Email sent"},
    )


class ErrorResponse(BaseModel):
    """Standard error response format across all apps."""
    status: int = Field(..., description="HTTP status code of the error")
    code: str = Field(..., description="Application-specific error identifier") 
    message: str = Field(..., description="Human-readable summary of the error")
    details: Optional[str] = Field(
        None, description="Additional information that may help resolve the error"
    )


class ErrorCode(str, Enum):
    invalid_request = "invalid_request"
    not_authenticated = "not_authenticated"
    not_authorized = "not_authorized"
    not_found = "not_found"
    server_error = "server_error"


class FoldersResponse(BaseModel):
    folders: list[str]


class EmailBody(BaseModel):
    body: str
