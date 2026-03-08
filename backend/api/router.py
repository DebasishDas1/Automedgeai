from fastapi import APIRouter
from api.v1 import health, leads, workflow, bookings, chat

router = APIRouter()

router.include_router(health.router, prefix="/health", tags=["health"])
router.include_router(leads.router, prefix="/leads", tags=["leads"])
router.include_router(workflow.router, prefix="/workflow", tags=["workflow"])
router.include_router(bookings.router, prefix="/bookings", tags=["bookings"])
router.include_router(chat.router, prefix="/chat", tags=["chat"])
