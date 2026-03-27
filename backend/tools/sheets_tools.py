# tools/sheets_tools.py
# Google Sheets delivery — Hot/Warm/Cold Leads tabs per vertical.
from __future__ import annotations

import asyncio
import json
import structlog
from typing import Any
from core.config import settings

logger = structlog.get_logger(__name__)

_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

_HEADER = [
    "Timestamp", "Name", "Email", "Phone",
    "Issue", "Description", "Urgency", "Address",
    "Score", "Summary", "Full Conversation", "Session ID",
]

# Module-level client cache — rebuilt only if credentials change
_sheets_svc = None


def _get_service():
    """
    Build and cache the Sheets API client.

    BUG FIX: original called _get_tools() (rebuilt the client from scratch)
    on every append. This re-parsed the JSON credentials and re-called
    googleapiclient.discovery.build() on every lead — expensive and
    unnecessary. Cached at module level.
    """
    global _sheets_svc
    if _sheets_svc is not None:
        return _sheets_svc

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
    except Exception as exc:
        raise RuntimeError(f"Invalid JSON in SHEETS_CREDENTIALS_JSON: {exc}")

    creds = Credentials.from_service_account_info(info, scopes=_SCOPES)
    _sheets_svc = build("sheets", "v4", credentials=creds)
    return _sheets_svc


class SheetsTools:

    async def append_lead(self, sheet_id: str, tab_name: str, row_data: list[Any]) -> None:
        """Append a row to the given tab. Creates the tab + header if missing."""
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
        svc = _get_service()

        # Ensure tab exists — best-effort, never blocks the append
        try:
            meta = svc.spreadsheets().get(spreadsheetId=sheet_id).execute()
            existing = {s["properties"]["title"] for s in meta["sheets"]}
            if tab_name not in existing:
                svc.spreadsheets().batchUpdate(
                    spreadsheetId=sheet_id,
                    body={"requests": [{"addSheet": {"properties": {"title": tab_name}}}]},
                ).execute()
                svc.spreadsheets().values().append(
                    spreadsheetId=sheet_id,
                    range=f"{tab_name}!A1",
                    valueInputOption="USER_ENTERED",
                    body={"values": [_HEADER]},
                ).execute()
        except Exception as exc:
            logger.warning("sheets_tab_create_failed", tab=tab_name, error=str(exc))

        svc.spreadsheets().values().append(
            spreadsheetId=sheet_id,
            range=f"{tab_name}!A:Z",
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body={"values": [row_data]},
        ).execute()


sheets_tools = SheetsTools()