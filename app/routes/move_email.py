from aioimaplib import aioimaplib, IMAP4_SSL
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict
from models import MoveEmailsRequest
from dependencies import (
    get_api_key,
    get_account_details,
)

move_router = APIRouter()


@move_router.post("/move_emails", operation_id="move_email")
async def move_emails(request: MoveEmailsRequest, api_key: str = Depends(get_api_key)):
    try:
        account_details = await get_account_details(request.account)
    except HTTPException as e:
        print(f"Error fetching account details: {e.detail}")
        raise HTTPException(status_code=404, detail="Account not found")

    try:
        mail = IMAP4_SSL(account_details["imap_server"])
        await mail.wait_hello_from_server()
        await mail.login(account_details["email"], account_details["password"])

        # Check server capabilities
        status, capabilities_data = await mail.capability()
        capabilities = capabilities_data[0].decode("utf-8").split()
        print(f"Server capabilities: {capabilities}")
        if "MOVE" not in capabilities:
            raise HTTPException(
                status_code=500, detail="MOVE command not supported by the server"
            )

        await mail.select(request.folder)
        target_folder = "Trash" if request.action == "trash" else "Spam"

        # Attempt to move the email
        result_status, move_data = await mail.uid(
            "MOVE", request.email_id, target_folder
        )
        if result_status != "OK":
            error_detail = (
                move_data[0].decode("utf-8")
                if move_data and isinstance(move_data[0], bytes)
                else str(move_data)
            )
            print(f"Failed to move email: {error_detail}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to move email to {target_folder}: {error_detail}",
            )
        print(f"Email moved to {target_folder} successfully")
        return {
            "status": "success",
            "detail": f"Email moved to {target_folder} successfully",
        }
    except Exception as e:
        print(f"Error moving email: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error moving email: {str(e)}")
    finally:
        await mail.logout()
