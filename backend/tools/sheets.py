import logging
from core.config import settings
from datetime import datetime

logger = logging.getLogger(__name__)


class SheetsTool:

    def save_lead_to_sheet(self, state: dict, sheet_id: str = "mock_sheet_id") -> int:
        tab = {
            "hot": "Hot Leads",
            "warm": "Warm Leads",
            "cold": "Cold Leads"
        }.get(state.get("score", "warm"), "Warm Leads")

        row = [
            datetime.now().isoformat(),
            state.get("name", ""),
            state.get("email", ""),
            state.get("phone", ""),
            state.get("location", ""),
            state.get("issue", ""),
            state.get("system_age", ""),
            state.get("urgency", ""),
            str(state.get("is_homeowner", "")),
            state.get("budget_signal", ""),
            (state.get("score", "")).upper(),
            str(state.get("score_number", "")),
            state.get("score_reason", ""),
            str(state.get("appt_booked", False)),
            state.get("appt_confirmed", ""),
            str(state.get("email_sent", False)),
            str(state.get("turn_count", 0)),
            state.get("summary", ""),
            state.get("session_id", ""),
        ]

        if settings.ENVIRONMENT != "production":
            logger.info(f"[MOCK SHEETS] tab={tab}\nrow={row}")
            return 99

        logger.info(f"Saving to real sheets tab {tab}")
        return 99


sheets_tool = SheetsTool()