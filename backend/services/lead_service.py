# services/lead_service.py
import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import Lead
from models.lead import LeadCreate, LeadUpdate, LeadResponse

logger = logging.getLogger(__name__)


async def create_lead(db: AsyncSession, data: LeadCreate) -> LeadResponse:
    row = Lead(
        name       = data.name,
        email      = data.email,
        phone      = data.phone,
        issue      = data.issue,
        address    = data.address,
        vertical   = data.vertical,
        appt_at    = data.appt_at,
        session_id = data.session_id,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return LeadResponse.model_validate(row)


async def upsert_from_chat(db: AsyncSession, session_id: str, state: dict) -> LeadResponse:
    """
    Create or update a lead from a completed chat session state.
    Called by workflow_service after post-chat graph finishes.
    """
    # Try to find existing row for this session
    result = await db.execute(select(Lead).where(Lead.session_id == session_id))
    row    = result.scalar_one_or_none()

    # Parse appt_at from confirmed slot string if present
    appt_at = None
    if state.get("appt_confirmed"):
        try:
            from datetime import datetime
            # Slot format: "Thursday, Mar 13 at 2:00 PM"
            appt_at = datetime.strptime(
                state["appt_confirmed"].split(", ", 1)[-1],   # "Mar 13 at 2:00 PM"
                "%b %d at %I:%M %p"
            ).replace(year=datetime.now().year)
        except Exception:
            pass  # appt_at stays None — raw string in issue is fine

    if row is None:
        row = Lead(
            session_id = session_id,
            vertical   = state.get("vertical", "hvac"),
        )
        db.add(row)

    row.name    = state.get("name")    or row.name
    row.email   = state.get("email")   or row.email
    row.phone   = state.get("phone")   or row.phone
    row.issue   = state.get("issue")   or row.issue
    row.address = state.get("location") or row.address
    row.appt_at = appt_at or row.appt_at

    await db.commit()
    await db.refresh(row)
    logger.info(f"lead upserted: session={session_id} vertical={row.vertical}")
    return LeadResponse.model_validate(row)


async def update_lead(db: AsyncSession, lead_id: UUID, data: LeadUpdate) -> LeadResponse | None:
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    row    = result.scalar_one_or_none()
    if row is None:
        return None
    for key, val in data.model_dump(exclude_none=True).items():
        setattr(row, key, val)
    await db.commit()
    await db.refresh(row)
    return LeadResponse.model_validate(row)


async def get_leads(
    db:       AsyncSession,
    vertical: str | None = None,
    limit:    int        = 50,
    offset:   int        = 0,
) -> list[LeadResponse]:
    q = select(Lead)
    if vertical:
        q = q.where(Lead.vertical == vertical)
    rows = (await db.execute(q.order_by(Lead.created_at.desc()).limit(limit).offset(offset))).scalars().all()
    return [LeadResponse.model_validate(r) for r in rows]