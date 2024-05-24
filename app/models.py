from pydantic import BaseModel, Field, EmailStr, conint, validator
from typing import Optional, List, Union
from dependencies import validate_account_sync


class SendEmailRequest(BaseModel):
    account: EmailStr = Field(
        ..., description="The email account that will be used to send the email."
    )
    to_address: Union[EmailStr, List[EmailStr]] = Field(
        ..., description="The recipient's email address or list of email addresses."
    )
    subject: str = Field(..., description="The subject of the email.", max_length=255)
    body: str = Field(..., description="The body content of the email.")
    folder: Optional[str] = Field(
        None,
        description="The folder where the original email is located (e.g., INBOX). This is optional and used only when replying to an email.",
    )
    email_id: Optional[str] = Field(
        None,
        description="The unique ID of the email being replied to. This is optional and used only when replying to an email.",
    )

    @validator("account")
    def validate_account(cls, value):
        validate_account_sync(value)
        return value

    @validator("to_address")
    def validate_to_address(cls, value):
        if isinstance(value, str):
            EmailStr.validate(value)
        elif isinstance(value, list):
            for email in value:
                EmailStr.validate(email)
        else:
            raise ValueError("Invalid email address format")
        return value


class ListFoldersAndEmailsRequest(BaseModel):
    account: EmailStr = Field(..., description="The email account to be used.")
    action: str = Field(
        ..., description="The action to perform: 'folders' or 'emails'."
    )
    folder: Optional[str] = Field(
        None,
        description="The folder from which to list emails. Required if action is 'emails'.",
    )
    limit: Optional[conint(gt=0, le=100)] = Field(
        None,
        description="The number of most recent emails to list. Used only when listing emails.",
    )

    @validator("account")
    def validate_account(cls, value):
        validate_account_sync(value)
        return value

    @validator("action")
    def validate_action(cls, value):
        if value not in ["folders", "emails"]:
            raise ValueError("Action must be either 'folders' or 'emails'")
        return value

    @validator("folder", always=True)
    def validate_folder(cls, value, values):
        if values.get("action") == "emails" and not value:
            raise ValueError("Folder must be provided when action is 'emails'")
        return value

    @validator("limit", always=True)
    def validate_limit(cls, value, values):
        if values.get("action") == "emails" and not value:
            raise ValueError("Limit must be provided when action is 'emails'")
        return value


class ReadEmailsRequest(BaseModel):
    account: EmailStr = Field(..., description="The email account to be used.")
    folder: str = Field(..., description="The folder containing the email to read.")
    email_id: str = Field(..., description="The ID of the email to read.")

    @validator("account")
    def validate_account(cls, value):
        validate_account_sync(value)
        return value


class MoveEmailsRequest(BaseModel):
    account: EmailStr = Field(..., description="The email account to be used.")
    folder: str = Field(..., description="The folder containing the email to move.")
    email_id: str = Field(..., description="The ID of the email to move.")
    action: str = Field(
        ..., description="The action to perform on the email (trash or spam)."
    )

    @validator("account")
    def validate_account(cls, value):
        validate_account_sync(value)
        return value

    @validator("action")
    def validate_action(cls, value):
        if value not in ["trash", "spam"]:
            raise ValueError("Action must be either 'trash' or 'spam'")
        return value
