from typing import TypedDict, Literal, Optional
from datetime import datetime

# Every vertical's graph uses this same state shape
class LeadState(TypedDict):
    lead_id:      str
    name:         str
    phone:        str
    email:        str
    source:       str          # google|angi|phone|web
    vertical:     str          # hvac|roofing|plumbing|pest
    issue:        str          # "AC not cooling"
    city:         str
    stage:        str          # new|contacted|quoted|booked|done
    sms_sent:     bool
    tech_notified:bool
    booked_at:    Optional[datetime]
    review_sent:  bool
    events:       list[dict]   # audit trail streamed to frontend

# Shared nodes every vertical uses
def capture_lead(state: LeadState) -> LeadState: ...
def send_sms(state: LeadState) -> LeadState: ...
def notify_tech(state: LeadState) -> LeadState: ...
def request_review(state: LeadState) -> LeadState: ...