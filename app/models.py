from pydantic import BaseModel, EmailStr, Field, HttpUrl
from typing import Union, List, Optional


class SendEmailRequest(BaseModel):
    to_address: Union[EmailStr, List[EmailStr]] = Field(
        ..., description="The recipient's email address or list of email addresses."
    )
    subject: str = Field(..., description="The subject of the email.", max_length=255)
    body: str = Field(..., description="The body content of the email.")
    file_url: Optional[Union[HttpUrl, List[HttpUrl]]] = Field(
        None,
        description="The URL or list of URLs of the files to be downloaded and attached to the email.",
    )
