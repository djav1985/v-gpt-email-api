import aioimaplib

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict

from models import MoveEmailsRequest
from dependencies import (
    get_api_key,
    get_account_details,
)

move_router = APIRouter()

@move_router.post("/move_emails", operation_id="move_email")
async def move_emails(
    request: MoveEmailsRequest, api_key: str = Depends(get_api_key)
):
    try:
        account_details = await get_account_details(request.account)
    except KeyError as e:
        raise HTTPException(status_code=404, detail="Account not found")

    try:
        async with aioimaplib.IMAP4_SSL(account_details["imap_server"]) as mail:
            await mail.login(account_details["email"], account_details["password"])

            # Check server capabilities
            status, capabilities_data = await mail.capability()
            capabilities = capabilities_data[0].decode("utf-8").split()
            if "MOVE" not in capabilities:
                raise HTTPException(
                    status_code=500, detail="MOVE command not supported by the server"
                )

            await mail.select(request.folder)
            target_folder = "Trash" if request.action == "trash" else "Spam"

            # Attempt to move the email
            result_status, move_data = await mail.uid("MOVE", request.email_id, target_folder)
            if result_status != "OK":
                error_detail = (
                    move_data[0].decode("utf-8")
                    if move_data and isinstance(move_data[0], bytes)
                    else str(move_data)
                )
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to move email to {target_folder}: {error_detail}",
                )
            return {
                "status": "success",
                "detail": f"Email moved to {target_folder} successfully",
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error moving email: {str(e)}")
