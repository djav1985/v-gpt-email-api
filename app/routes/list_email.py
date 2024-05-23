from fastapi import APIRouter, Depends, HTTPException
from models import ListFoldersAndEmailsRequest
from dependencies import (
    get_api_key,
    get_account_details,
    decode_header_value,
    fetch_email,
    get_email_body,
    send_email_utility,
)
import imaplib
from email import message_from_bytes

list_router = APIRouter()


@list_router.post("/list_folders_and_emails", operation_id="list_folders_and_emails")
async def list_folders_and_emails(
    request: ListFoldersAndEmailsRequest, api_key: str = Depends(get_api_key)
):
    try:
        account_details = await get_account_details(request.account)
    except HTTPException as e:
        raise HTTPException(status_code=404, detail="Account not found")

    if request.action == "folders":
        # List folders
        try:
            with aioimaplib.IMAP4_SSL(account_details["imap_server"]) as mail:
                await mail.login(account_details["email"], account_details["password"])
                status, folder_list = await mail.list()
                if status != "OK":
                    raise HTTPException(
                        status_code=500, detail="Failed to list folders"
                    )

                folders = []
                for folder in folder_list:
                    parts = folder.decode("utf-8").split(" ")
                    folder_name = " ".join(parts[2:]).strip('"')
                    folders.append(folder_name)

                return {"folders": folders}
        except aioimaplib.IMAP4.error as e:
            raise HTTPException(
                status_code=500, detail=f"Error listing folders: {str(e)}"
            )

    elif request.action == "emails":
        # List emails in the specified folder
        try:
            with aioimaplib.IMAP4_SSL(account_details["imap_server"]) as mail:
                await mail.login(account_details["email"], account_details["password"])
                await mail.select(request.folder)
                status, data = await mail.uid("search", None, "ALL")
                if status != "OK":
                    raise HTTPException(
                        status_code=500, detail="Failed to search emails"
                    )

                email_ids = data[0].split()[-request.limit :]
                emails = []
                for email_id in email_ids:
                    typ, email_data = await mail.uid("fetch", email_id, "(RFC822)")
                    if typ != "OK":
                        continue

                    email_msg = message_from_bytes(email_data[0][1])
                    subject = await decode_header_value(email_msg["Subject"])
                    from_header = await decode_header_value(email_msg["From"])
                    date_header = await decode_header_value(email_msg["Date"])

                    if email_msg.is_multipart():
                        body = "".join(
                            part.get_payload(decode=True).decode("utf-8")
                            for part in email_msg.get_payload()
                            if part.get_content_type() == "text/plain"
                        )
                    else:
                        body = email_msg.get_payload(decode=True).decode("utf-8")

                    emails.append(
                        {
                            "email_id": email_id.decode("utf-8").strip(),
                            "subject": subject,
                            "from": from_header,
                            "date": date_header,
                            "body_preview": body[:50],
                        }
                    )

                return {"emails": emails}
        except aioimaplib.IMAP4.error as e:
            raise HTTPException(
                status_code=500, detail=f"Error fetching emails: {str(e)}"
            )
