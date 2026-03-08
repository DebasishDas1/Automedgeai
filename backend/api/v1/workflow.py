from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from api.deps import get_db, get_current_user
from services.lead_service import LeadService
from services.workflow_service import workflow_service
from uuid import UUID

router = APIRouter()

@router.post("/{lead_id}/run")
async def start_workflow(
    lead_id: UUID,
    db: AsyncSession = Depends(get_db),
    user = Depends(get_current_user)
):
    lead = await LeadService.get_lead(db, lead_id)
    if not lead or lead.user_id != user["uid"]:
        raise HTTPException(404, "Lead not found")

    # Convert Lead DB model to dict for LangGraph
    state = {
        "lead_id": str(lead.id),
        "name": lead.name,
        "phone": lead.phone,
        "email": lead.email,
        "source": lead.source,
        "vertical": lead.vertical,
        "issue": lead.issue,
        "city": lead.city,
        "stage": lead.stage,
        "sms_sent": lead.sms_sent,
        "tech_notified": lead.tech_notified,
        "booked_at": lead.booked_at,
        "review_sent": lead.review_sent,
        "events": []
    }

    return StreamingResponse(
        workflow_service.stream_workflow(lead.vertical, state),
        media_type="text/event-stream"
    )
