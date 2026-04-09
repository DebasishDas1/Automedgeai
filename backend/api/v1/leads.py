# api/v1/leads.py
import structlog
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from models.lead import LeadCreate, LeadUpdate, LeadResponse, LeadListResponse
from tools import lead_tools

logger = structlog.get_logger(__name__)
router = APIRouter()


@router.post("/", response_model=LeadResponse, status_code=201)
async def create_lead(body: LeadCreate, db: AsyncSession = Depends(get_db)):
    try:
        return await lead_tools.create_lead(db, body)
    except ValueError as e:
        logger.warning("create_lead_validation_error", error_type=type(e).__name__)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("create_lead_failed", error_type=type(e).__name__)
        raise HTTPException(status_code=500, detail="Failed to create lead.")


@router.get("/", response_model=LeadListResponse)
async def list_leads(
    vertical: str | None = Query(None, max_length=50),
    score:    str | None = Query(None, max_length=50),
    stage:    str | None = Query(None, max_length=50),
    limit:    int        = Query(50, ge=1, le=200),
    offset:   int        = Query(0, ge=0),
    db: AsyncSession     = Depends(get_db),
):
    try:
        leads, total = await lead_tools.get_leads(db, vertical, score, stage, limit, offset)
        return LeadListResponse(leads=leads, total=total)
    except Exception as e:
        logger.error("list_leads_failed", error_type=type(e).__name__)
        raise HTTPException(status_code=500, detail="Failed to fetch leads.")


@router.patch("/{lead_id}", response_model=LeadResponse)
async def update_lead(
    lead_id: UUID,
    body:    LeadUpdate,
    db:      AsyncSession = Depends(get_db),
):
    try:
        result = await lead_tools.update_lead(db, lead_id, body)
    except ValueError as e:
        logger.warning("update_lead_validation_error", error_type=type(e).__name__)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("update_lead_failed", error_type=type(e).__name__)
        raise HTTPException(status_code=500, detail="Failed to update lead.")
    if result is None:
        raise HTTPException(status_code=404, detail=f"Lead not found: {lead_id}")
    return result