"""Application configuration settings."""

from pydantic import EmailStr
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    """Application configuration loaded from environment variables."""

    account_email: EmailStr
    account_password: str
    account_smtp_server: str
    account_smtp_port: int
    account_imap_server: str
    account_imap_port: int
    api_key: str | None = None
    from_name: str = ""
    attachment_concurrency: int = 3
    start_tls: bool = True
    account_reply_to: EmailStr | None = None
