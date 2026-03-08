from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from uuid import UUID

class BookingBase(BaseModel):
    name: str
    email: EmailStr
    business: str
    vertical: str
    team_size: Optional[str] = None

class BookingCreate(BookingBase):
    pass

class Booking(BookingBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True
