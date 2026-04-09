# tools/booking_tools.py
# Booking-specific logic for appointments and calendar integration.
from __future__ import annotations

import structlog
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import Booking
from models.booking import BookingCreate
from core.config import settings

logger = structlog.get_logger(__name__)

async def create_booking(db: AsyncSession, data: BookingCreate) -> Booking:
    """
    Persist a new demo booking to the database and trigger notifications.
    """
    log = logger.bind(vertical=data.vertical)
    
    try:
        # 1. Validate input
        if not data.name or not data.email or not data.business:
            raise ValueError("name, email, and business are required fields")
        
        # 2. Create DB record
        new_booking = Booking(
            name=data.name.strip(),
            email=data.email.strip(),
            business=data.business.strip(),
            vertical=data.vertical,
            team_size=data.team_size.strip() if data.team_size else None,
            message=data.message.strip() if data.message else None,
            scheduled_at=data.scheduled_at,
        )
        db.add(new_booking)
        await db.commit()
        await db.refresh(new_booking)
        
        log.info("booking_persisted", id=str(new_booking.id))
        
        # 3. Optional notification (implement if needed)
        try:
            from tools.email_tools import email_tools
            # Construct a small state dict for the existing email tool or implement a custom one
            # For now, let's just log it. If you want full email integration, we'd add it here.
            pass 
        except Exception as e:
            log.warning("booking_notification_failed", error_type=type(e).__name__)

        return new_booking

    except Exception as e:
        log.error("create_booking_failed", error_type=type(e).__name__)
        await db.rollback()
        raise e

def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()