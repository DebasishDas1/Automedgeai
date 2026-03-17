# api/router.py
from fastapi import APIRouter
from api.v1.chat import router as chat_router

router = APIRouter()

# High-performance chat workflow (consolidated strategy)
router.include_router(chat_router, prefix="/chat")