import logging
from core.config import settings
from datetime import datetime

logger = logging.getLogger(__name__)


class SheetsTool:

    def save_lead_to_sheet(self, state: dict, sheet_id: str = "mock_sheet_id") -> int:

        score = state.get("score", "warm")

        tab = {
            "hot": "Hot Leads",
            "warm": "Warm Leads",
            "cold": "Cold Leads"
        }.get(score, "Warm Leads")

        row = [
            datetime.utcnow().isoformat(),

            state.get("name", ""),
            state.get("email", ""),
            state.get("phone", ""),

            state.get("city", "") or state.get("location", ""),

            state.get("issue", ""),
            state.get("system_age", ""),
            state.get("urgency", ""),

            str(state.get("is_homeowner", "")),
            state.get("budget_signal", ""),

            score.upper(),
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
            logger.info(f"[MOCK SHEETS]\ntab={tab}\nrow={row}")
            return 99

        try:
            # future real implementation
            logger.info(f"Saving lead to Google Sheet → tab={tab}")

            # placeholder until API added
            return 99

        except Exception as e:
            logger.exception("Sheet write failed")
            return -1


sheets_tool = SheetsTool()