# api/router.py
from fastapi import APIRouter
from api.v1 import leads, workflow, bookings
from api.v1.chat import router as chat_router

router = APIRouter()

router.include_router(leads.router,    prefix="/leads",    tags=["leads"])
router.include_router(workflow.router, prefix="/workflow",  tags=["workflow"])
router.include_router(bookings.router, prefix="/bookings", tags=["bookings"])
router.include_router(chat_router,     prefix="/chat")   # ← prefix required

# POST  /api/v1/chat/hvac/start
# POST  /api/v1/chat/hvac/message
# POST  /api/v1/chat/pest-control/start
# POST  /api/v1/chat/pest-control/message
# POST  /api/v1/chat/plumbing/start
# POST  /api/v1/chat/plumbing/message
# POST  /api/v1/chat/roofing/start
# POST  /api/v1/chat/roofing/message
# POST  /api/v1/leads/
# GET   /api/v1/leads/
# PATCH /api/v1/leads/{id}
# POST  /api/v1/workflow/start
# GET   /api/v1/workflow/stream/{id}
# POST  /api/v1/bookings/