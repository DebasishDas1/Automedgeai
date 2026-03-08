from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from models.lead import LeadCreate, LeadUpdate
from core.database import Lead, WorkflowEvent
from models.workflow import WorkflowEventCreate
from uuid import UUID
import datetime

class LeadService:
    @staticmethod
    async def create_lead(db: AsyncSession, lead_in: LeadCreate, user_id: str) -> Lead:
        db_lead = Lead(
            **lead_in.model_dump(),
            user_id=user_id,
            stage="new",
            urgency="normal"
        )
        db.add(db_lead)
        await db.commit()
        await db.refresh(db_lead)
        return db_lead

    @staticmethod
    async def get_lead(db: AsyncSession, lead_id: UUID) -> Lead | None:
        result = await db.execute(select(Lead).where(Lead.id == lead_id))
        return result.scalars().first()

    @staticmethod
    async def get_user_leads(db: AsyncSession, user_id: str) -> list[Lead]:
        result = await db.execute(select(Lead).where(Lead.user_id == user_id).order_by(Lead.created_at.desc()))
        return result.scalars().all()

    @staticmethod
    async def update_lead(db: AsyncSession, lead_id: UUID, lead_in: LeadUpdate) -> Lead | None:
        db_lead = await LeadService.get_lead(db, lead_id)
        if not db_lead:
            return None
        
        update_data = lead_in.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_lead, key, value)
        
        await db.commit()
        await db.refresh(db_lead)
        return db_lead

    @staticmethod
    async def add_workflow_event(db: AsyncSession, event_in: WorkflowEventCreate) -> WorkflowEvent:
        db_event = WorkflowEvent(
            **event_in.model_dump()
        )
        db.add(db_event)
        await db.commit()
        await db.refresh(db_event)
        return db_event

    @staticmethod
    async def get_workflow_events(db: AsyncSession, lead_id: UUID) -> list[WorkflowEvent]:
        result = await db.execute(select(WorkflowEvent).where(WorkflowEvent.lead_id == lead_id).order_by(WorkflowEvent.step.asc()))
        return result.scalars().all()
