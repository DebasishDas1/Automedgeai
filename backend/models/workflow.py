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
