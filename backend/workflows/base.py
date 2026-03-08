from typing import TypedDict, Literal, Optional
from datetime import datetime
from tools.sheets import sheets_tool
from tools.sms import sms_tool
from tools.review import review_tool
import logging

logger = logging.getLogger(__name__)

# Every vertical's graph uses this same state shape
class LeadState(TypedDict):
    lead_id:      str
    name:         str
    phone:        str
    email:        str
    source:       str          # google|angi|phone|web
    vertical:     str          # hvac|roofing|plumbing|pest
    issue:        str          # "AC not cooling"
    urgency:      str          # emergency|urgent|normal
    city:         str
    stage:        str          # new|contacted|quoted|booked|done
    sms_sent:     bool
    tech_notified:bool
    booked_at:    Optional[datetime]
    review_sent:  bool
    events:       list[dict]   # audit trail streamed to frontend

def add_event(state: LeadState, label: str, status: str = "done") -> None:
    step_num = len(state.get("events", [])) + 1
    state.get("events", []).append({
        "step": step_num,
        "label": label,
        "status": status,
        "timestamp_str": "now" # In real app, calculate from start
    })

# Shared nodes every vertical uses
def capture_lead(state: LeadState) -> LeadState:
    logger.info(f"Node [capture_lead] for {state['name']}")
    
    # Save to Google Sheets
    row = [
        datetime.now().isoformat(),
        state['name'],
        state['phone'],
        state['email'],
        state['source'],
        state['issue'],
        state['city']
    ]
    sheets_tool.append_row(state['vertical'], row)
    
    add_event(state, "Lead Captured & Validated", "done")
    state['stage'] = "contacted"
    return state

def send_sms(state: LeadState) -> LeadState:
    logger.info(f"Node [send_sms] to {state['phone']}")
    
    message = f"Hi {state['name']}, thanks for reaching out to Automedge about your {state['vertical']} issue. A technician will contact you shortly."
    success = sms_tool.send_sms(state['phone'], message)
    
    state['sms_sent'] = success
    add_event(state, "SMS Notification Sent", "done" if success else "error")
    return state

def request_review(state: LeadState) -> LeadState:
    logger.info(f"Node [request_review] for {state['name']}")
    
    success = review_tool.request_review(state['name'], state['email'], state['phone'])
    
    state['review_sent'] = success
    add_event(state, "Review Request Sent", "done" if success else "error")
    return state