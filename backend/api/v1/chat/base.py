# api/v1/chat/base.py
# Shared request/response models and handler functions.
# Each vertical router calls these — no logic is duplicated.
#
# NO /status endpoint — sheets, email, scoring all run automatically
# as a BackgroundTask the moment is_complete=True is returned.
# The frontend gets everything it needs from /message responses.
from __future__ import annotations
import logging
from typing import Literal

from fastapi import BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel, Field

from core.database import get_db
from services import workflow_service
logger = logging.getLogger(__name__)

Vertical = Literal["hvac", "pest_control", "plumbing", "roofing"]


# ── Request / Response models ─────────────────────────────────────────────────

class StartRequest(BaseModel):
    source:   str | None = Field(None, description="Lead source e.g. google_lsa, angi, web_form")
    metadata: dict | None = Field(None, description="Optional KV pairs attached to the session")


class StartResponse(BaseModel):
    session_id: str
    vertical:   Vertical
    turn:       int = 0


class MessageRequest(BaseModel):
    session_id: str
    message:    str = Field(..., min_length=1, max_length=2000)


class MessageResponse(BaseModel):
    session_id:       str
    message:          str   # AI reply
    turn:             int
    is_complete:      bool
    appt_booked:      bool
    fields_collected: dict  # non-null fields collected so far


# ── Shared handlers — called by each vertical router ─────────────────────────
# Keeping the vertical as a fixed string per router means each endpoint
# is self-contained and readable while sharing all actual logic here.

async def handle_start(vertical: Vertical, body: StartRequest, db) -> StartResponse:
    try:
        result = await workflow_service.start_session(
            db       = db,
            vertical = vertical,
            source   = body.source,
            metadata = body.metadata,
        )
    except Exception as e:
        logger.error(f"start_chat failed: vertical={vertical} error={e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start chat session. Please try again.",
        )
    return StartResponse(
        session_id = result["session_id"],
        vertical   = vertical,
        turn       = result["turn"],
    )


async def handle_message(
    body:             MessageRequest,
    background_tasks: BackgroundTasks,
    db,
) -> MessageResponse:
    try:
        result = await workflow_service.send_message(
            db         = db,
            session_id = body.session_id,
            user_msg   = body.message,
        )
    except ValueError as e:
        msg = str(e)
        if "not found" in msg:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg)
        if "already complete" in msg:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)
    except Exception as e:
        logger.error(f"send_message failed: session={body.session_id} error={e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process message. Please try again.",
        )

    # When conversation ends: run post-chat graph in background.
    # This handles scoring + email + sheets automatically — no separate endpoint needed.
    if result["is_complete"]:
        logger.info(f"Chat complete — running post-chat: session={body.session_id}")
        background_tasks.add_task(
            workflow_service.run_post_chat,
            state    = result["_state"],
            vertical = result["_vertical"],
        )

    return MessageResponse(
        session_id       = body.session_id,
        message          = result["message"],
        turn             = result["turn"],
        is_complete      = result["is_complete"],
        appt_booked      = result["appt_booked"],
        fields_collected = result["fields_collected"],
    )