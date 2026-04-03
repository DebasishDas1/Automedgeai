# api/v1/retell.py
# Retell AI post-call webhook endpoint.
from __future__ import annotations

import hmac
import hashlib
import json
import asyncio
import structlog

from fastapi import APIRouter, BackgroundTasks, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from core.config import settings
from tools.retell_tools import extract_call_data
from tools.retell_delivery_tools import run_retell_post_call_pipeline

logger = structlog.get_logger(__name__)

router = APIRouter()


class WebCallRequest(BaseModel):
    type: str | None = None

class WebCallResponse(BaseModel):
    access_token: str
    call_id: str


@router.post(
    "/create-web-call",
    response_model=WebCallResponse,
    summary="Create a new web call session",
)
async def create_web_call(request: Request, payload: WebCallRequest | None = None):
    """
    Called by the frontend to get an access token for starting a web call.
    """
    if not settings.RETELL_API_KEY:
        raise HTTPException(status_code=500, detail="RETELL_API_KEY not configured")
    if not settings.RETELL_AGENT_ID:
        raise HTTPException(status_code=500, detail="RETELL_AGENT_ID not configured")

    try:
        client = request.app.state.retell

        dynamic_variables = {}
        if payload and payload.type:
            dynamic_variables["industry"] = payload.type

        web_call_response = await asyncio.to_thread(
            client.web_call.create,
            agent_id=settings.RETELL_AGENT_ID,
            retell_llm_dynamic_variables=dynamic_variables if dynamic_variables else None,
        )

        return {
            "access_token": web_call_response.access_token,
            "call_id": web_call_response.call_id,
        }
    except Exception as exc:
        logger.error("retell_create_web_call_failed", error=str(exc))
        raise HTTPException(status_code=500, detail=str(exc))


@router.post(
    "/post-call",
    operation_id="retell_post_call",
    summary="Retell AI post-call webhook",
    response_description="Accepted for async processing",
)
async def retell_post_call(
    request: Request,
    background_tasks: BackgroundTasks,
) -> JSONResponse:
    """
    Retell post-call webhook handler.
    Secured with HMAC-SHA256 signature verification.
    Offloads delivery to background task.
    """
    signature = request.headers.get("x-retell-signature")
    body = await request.body()

    # 1. HMAC Verification
    # FIX: Original used `hmac.new(key, msg, digestmod).hexdigest()` which is
    # correct but compares the raw hex string against the header value.
    # Retell sends the signature as a hex string, so this is fine.
    # However, hmac.compare_digest requires both operands to be the same type
    # (both str or both bytes). We ensure both are str here.
    if signature and settings.RETELL_WEBHOOK_SECRET:
        expected = hmac.new(
            settings.RETELL_WEBHOOK_SECRET.encode(),
            body,
            hashlib.sha256,
        ).hexdigest()  # str

        # FIX: Ensure signature from header is also str (it always is from HTTP
        # headers, but be explicit). hmac.compare_digest raises TypeError if
        # types differ.
        if not hmac.compare_digest(str(signature), expected):
            logger.warning("retell_webhook_invalid_signature")
            raise HTTPException(status_code=401, detail="invalid_signature")
    elif not signature and settings.ENVIRONMENT != "dev":
        raise HTTPException(status_code=401, detail="missing_signature")

    if not body:
        return JSONResponse({"status": "ok", "detail": "empty_body"})

    try:
        payload = json.loads(body)
    except Exception as exc:
        logger.warning("retell_webhook_bad_json", error=str(exc))
        return JSONResponse({"status": "error", "detail": "invalid_json"}, status_code=200)

    # 2. Extract Event
    event   = (payload.get("event") or payload.get("body", {}).get("event") or "")
    call_id = ((payload.get("call") or {}).get("call_id") or payload.get("call_id") or "unknown")

    logger.info("retell_webhook_received", event=event, call_id=call_id)

    if event != "call_analyzed":
        return JSONResponse({"status": "ignored", "event": event})

    # 3. Extract & enqueue
    try:
        call_data = extract_call_data(payload)
    except Exception as exc:
        logger.error("retell_extraction_failed", call_id=call_id, error=str(exc))
        return JSONResponse({"status": "extraction_failed", "call_id": call_id})

    background_tasks.add_task(_run_pipeline, call_data)

    return JSONResponse({
        "status": "accepted",
        "call_id": call_data["call_id"],
        "appointment_booked": call_data["appointment_booked"],
    })


async def _run_pipeline(call_data: dict) -> None:
    """Background task for post-call processing."""
    try:
        results = await run_retell_post_call_pipeline(call_data)
        logger.info("retell_pipeline_done", call_id=call_data["call_id"], results=results)
    except Exception as exc:
        logger.error("retell_pipeline_error", call_id=call_data.get("call_id"), error=str(exc))