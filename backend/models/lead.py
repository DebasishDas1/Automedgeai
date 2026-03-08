from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from uuid import UUID

class LeadBase(BaseModel):
    name: str
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    source: str
    vertical: str
    issue: Optional[str] = None
    city: Optional[str] = None

class LeadCreate(LeadBase):
    pass

class LeadUpdate(BaseModel):
    stage: Optional[str] = None
    urgency: Optional[str] = None
    sms_sent: Optional[bool] = None
    tech_notified: Optional[bool] = None
    booked_at: Optional[datetime] = None
    review_sent: Optional[bool] = None

class Lead(LeadBase):
    id: UUID
    stage: str
    urgency: str
    sms_sent: bool
    tech_notified: bool
    booked_at: Optional[datetime] = None
    review_sent: bool
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
