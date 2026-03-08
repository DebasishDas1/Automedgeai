from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from api.deps import get_db
from models.booking import BookingCreate, Booking
from core.database import Booking as BookingDB

router = APIRouter()

@router.post("/", response_model=Booking)
async def create_booking(
    booking_in: BookingCreate,
    db: AsyncSession = Depends(get_db)
):
    db_booking = BookingDB(**booking_in.model_dump())
    db.add(db_booking)
    await db.commit()
    await db.refresh(db_booking)
    return db_booking
