from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from uuid import UUID

class WorkflowEventBase(BaseModel):
    step: int
    label: str
    status: str
    timestamp_str: Optional[str] = None

class WorkflowEventCreate(WorkflowEventBase):
    lead_id: UUID

class WorkflowEvent(WorkflowEventBase):
    id: UUID
    lead_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True

class WorkflowStreamEvent(BaseModel):
    type: str # "event" | "error" | "complete"
    data: dict

from typing import TypedDict, List, Optional

class HVACChatState(TypedDict):
    # Session
    session_id: str
    user_id: Optional[str]
    started_at: str

    # Conversation
    messages: List[dict]
    turn_count: int
    is_complete: bool

    # Extracted lead data
    name: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    location: Optional[str]
    issue: Optional[str]
    system_age: Optional[str]
    urgency: Optional[str]
    is_homeowner: Optional[bool]
    budget_signal: Optional[str]
    timeline: Optional[str]

    # Appointment
    appt_offered: bool
    appt_slots: List[str]
    appt_confirmed: Optional[str]
    appt_booked: bool

    # Post-chat results
    summary: Optional[str]
    score: Optional[str]
    score_reason: Optional[str]
    email_sent: bool
    sheet_row: Optional[int]
    sheet_tab: Optional[str]
