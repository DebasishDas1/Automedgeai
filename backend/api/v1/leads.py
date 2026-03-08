from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from api.deps import get_db, get_current_user
from services.lead_service import LeadService
from models.lead import LeadCreate, LeadUpdate, Lead
from uuid import UUID

router = APIRouter()

@router.post("/", response_model=Lead)
async def create_lead(
    lead_in: LeadCreate,
    db: AsyncSession = Depends(get_db),
    user = Depends(get_current_user)
):
    return await LeadService.create_lead(db, lead_in, user["uid"])

@router.get("/", response_model=list[Lead])
async def get_leads(
    db: AsyncSession = Depends(get_db),
    user = Depends(get_current_user)
):
    return await LeadService.get_user_leads(db, user["uid"])

@router.get("/{lead_id}", response_model=Lead)
async def get_lead(
    lead_id: UUID,
    db: AsyncSession = Depends(get_db),
    user = Depends(get_current_user)
):
    lead = await LeadService.get_lead(db, lead_id)
    if not lead or lead.user_id != user["uid"]:
        raise HTTPException(404, "Lead not found")
    return lead

@router.patch("/{lead_id}", response_model=Lead)
async def update_lead(
    lead_id: UUID,
    lead_in: LeadUpdate,
    db: AsyncSession = Depends(get_db),
    user = Depends(get_current_user)
):
    lead = await LeadService.get_lead(db, lead_id)
    if not lead or lead.user_id != user["uid"]:
        raise HTTPException(404, "Lead not found")
    return await LeadService.update_lead(db, lead_id, lead_in)
