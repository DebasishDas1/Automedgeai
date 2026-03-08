from fastapi import Depends, HTTPException, Header
from core.firebase import verify_token
from core.database import get_db

async def get_current_user(authorization: str = Header(...)):
    token = authorization.replace("Bearer ", "")
    user = verify_token(token)       # firebase-admin verify
    if not user:
        raise HTTPException(401, "Invalid token")
    return user

# Usage in any route:
# async def get_leads(user = Depends(get_current_user)):