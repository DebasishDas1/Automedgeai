from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

@router.get("/health")
async def health_check():
    return {"status": "ok", "service": "automedge-api"}
