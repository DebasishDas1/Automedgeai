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
    operation_id="retell_webhook_post_call",
    summary="Retell AI post-call webhook",
    status_code=200,
)
async def retell_post_call(
    request: Request,
    background_tasks: BackgroundTasks,
) -> JSONResponse:
    """
    Handles Retell AI webhooks for call analysis.
    Verifies x-retell-signature using HMAC-SHA256 for security.
    Offloads CRM/Sheets/Twilio processing to an async background task.
    """
    signature = request.headers.get("x-retell-signature")
    body = await request.body()

    # 1. Signature Verification (HMAC-SHA256)
    if settings.RETELL_WEBHOOK_SECRET:
        if not signature:
             raise HTTPException(status_code=401, detail="missing_signature")
        
        expected = hmac.new(
            settings.RETELL_WEBHOOK_SECRET.encode(),
            body,
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(signature, expected):
            logger.warning("retell_auth_failed", sig=signature[:8])
            raise HTTPException(status_code=401, detail="invalid_signature")

    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        return JSONResponse({"status": "bad_json"}, status_code=400)

    # 2. Extract Event & ID
    event   = payload.get("event") or (payload.get("body", {}).get("event"))
    call_id = (payload.get("call", {}).get("call_id") or payload.get("call_id", "unknown"))

    # We only care when the call analysis is ready (transcript/summary finished)
    if event != "call_analyzed":
        return JSONResponse({"status": "ignored", "event": event})

    # 3. Analyze & Enqueue
    logger.info("retell_analyzing", call_id=call_id)
    try:
        call_data = extract_call_data(payload)
        
        # Enqueue heavy I/O (HubSpot, Sheets, Twilio)
        background_tasks.add_task(
            _run_pipeline,
            call_data,
            request.app.state.twilio,
            request.app.state.resend
        )

        return JSONResponse({
            "status": "accepted",
            "call_id": call_id,
            "booked": call_data.get("appointment_booked", False)
        })

    except Exception as exc:
        logger.error("retell_webhook_error", call_id=call_id, error=str(exc))
        return JSONResponse({"status": "error", "detail": "processing_failed"}, status_code=500)


async def _run_pipeline(call_data: dict, twilio_client=None, resend_client=None) -> None:
    """Background task for post-call delivery pipeline."""
    try:
        results = await run_retell_post_call_pipeline(call_data, twilio_client, resend_client)
        logger.info("retell_pipeline_success", call_id=call_data.get("call_id"), results=results)
    except Exception as exc:
        logger.error("retell_pipeline_failed", call_id=call_data.get("call_id"), error=str(exc))