# services/sheets_tools.py
# Google Sheets delivery — 3 tabs: Hot Leads / Warm Leads / Cold Leads
from __future__ import annotations

import asyncio
import json
import structlog
from typing import Any
from core.config import settings

logger = structlog.get_logger(__name__)

_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def _get_tools():
    """Build Sheets API client from JSON env var."""
    try:
        from google.oauth2.service_account import Credentials
        from googleapiclient.discovery import build
    except ImportError:
        raise RuntimeError("Run: uv add google-api-python-client google-auth")

    raw = settings.SHEETS_CREDENTIALS_JSON
    if not raw:
        raise RuntimeError("SHEETS_CREDENTIALS_JSON env var not set")

    try:
        info = json.loads(raw)
    except Exception as e:
        raise RuntimeError(f"Invalid JSON in SHEETS_CREDENTIALS_JSON: {e}")

    creds = Credentials.from_service_account_info(info, scopes=_SCOPES)
    return build("sheets", "v4", credentials=creds)


class SheetsTools:

    async def append_lead(
        self,
        sheet_id: str,
        tab_name: str,
        row_data: list[Any],
    ) -> None:
        """Append a row to the given tab. Creates tab if missing."""
        if not sheet_id:
            logger.warning("sheets_skip_no_sheet_id", tab=tab_name)
            return
        try:
            await asyncio.to_thread(self._append_sync, sheet_id, tab_name, row_data)
            logger.info("sheets_row_appended", tab=tab_name)
        except Exception as exc:
            logger.error("sheets_append_failed", error=str(exc), tab=tab_name)
            raise

    def _append_sync(self, sheet_id: str, tab_name: str, row_data: list[Any]) -> None:
        svc = _get_tools()
        # Ensure tab exists
        try:
            meta = svc.spreadsheets().get(spreadsheetId=sheet_id).execute()
            existing = [s["properties"]["title"] for s in meta["sheets"]]
            if tab_name not in existing:
                svc.spreadsheets().batchUpdate(
                    spreadsheetId=sheet_id,
                    body={"requests": [{"addSheet": {"properties": {"title": tab_name}}}]},
                ).execute()
                # Add header row on new tab
                header = [
                    "Timestamp", "Name", "Email", "Phone",
                    "Issue", "Description", "Urgency", "Address",
                    "Score", "Summary", "Full Conversation", "Session ID"
                ]
                svc.spreadsheets().values().append(
                    spreadsheetId=sheet_id,
                    range=f"{tab_name}!A1",
                    valueInputOption="USER_ENTERED",
                    body={"values": [header]},
                ).execute()
        except Exception:
            pass  # best-effort tab creation

        svc.spreadsheets().values().append(
            spreadsheetId=sheet_id,
            range=f"{tab_name}!A:Z",
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body={"values": [row_data]},
        ).execute()


sheets_tools = SheetsTools()