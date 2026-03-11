# models/lead.py
from __future__ import annotations
import uuid
from datetime import datetime
from pydantic import BaseModel
from typing import List


class LeadCreate(BaseModel):
    name:       str | None = None
    email:      str | None = None
    phone:      str | None = None
    issue:      str | None = None
    address:    str | None = None   # city / zip / full address
    vertical:   str                 # hvac|roofing|plumbing|pest_control
    appt_at:    datetime | None = None
    session_id: str | None = None


class LeadUpdate(BaseModel):
    name:    str | None = None
    email:   str | None = None
    phone:   str | None = None
    issue:   str | None = None
    address: str | None = None
    appt_at: datetime | None = None


class LeadResponse(BaseModel):
    id:         uuid.UUID
    name:       str | None
    email:      str | None
    phone:      str | None
    issue:      str | None
    address:    str | None
    vertical:   str
    appt_at:    datetime | None
    session_id: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class LeadListResponse(BaseModel):
    leads: List[LeadResponse]
    total: int