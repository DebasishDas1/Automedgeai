# api/v1/bookings.py
import structlog

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from models.booking import BookingCreate, BookingResponse
from tools import booking_tools

logger = structlog.get_logger(__name__)
router = APIRouter()


@router.post("/", response_model=BookingResponse, status_code=201)
async def create_booking(body: BookingCreate, db: AsyncSession = Depends(get_db)):
    try:
        result = await booking_tools.create_booking(db, body)
        # Convert DB row to response model
        return BookingResponse.model_validate(result)
    except ValueError as e:
        logger.warning("create_booking_validation_error", error_type=type(e).__name__)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("create_booking_failed", error_type=type(e).__name__)
        raise HTTPException(status_code=500, detail="Failed to save booking.")