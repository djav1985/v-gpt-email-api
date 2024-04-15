from fastapi import HTTPException

def get_account_details(email: str, accounts):
    account_details = next((acc for acc in accounts if acc['email'] == email), None)
    if not account_details:
        raise HTTPException(status_code=404, detail="Account not found")
    return account_details
