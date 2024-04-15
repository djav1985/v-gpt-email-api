from fastapi import HTTPException

# Assuming 'accounts' is available here, either by passing it to the function or by importing
def get_account_details(email: str, accounts):
    account_details = next((acc for acc in accounts if acc['email'] == email), None)
    if not account_details:
        raise HTTPException(status_code=404, detail="Account not found")
    return account_details
