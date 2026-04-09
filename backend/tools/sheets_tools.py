# tools/sheets_tools.py
# Consolidated Google Sheets delivery using gspread.
from __future__ import annotations

import asyncio
import structlog
from typing import Any
from core.sheets import get_sheets_client

logger = structlog.get_logger(__name__)

_HEADER = [
    "Timestamp", "Name", "Email", "Phone",
    "Issue", "Description", "Urgency", "Address",
    "Score", "Summary", "Full Conversation", "Session ID",
]

class SheetsTools:
    async def append_lead(self, sheet_id: str, tab_name: str, row_data: list[Any], app_state=None) -> None:
        """Append a row to the given tab. Creates the tab + header if missing."""
        if not sheet_id:
            logger.warning("sheets_skip_no_sheet_id", tab=tab_name)
            return
        try:
            # Delegate to thread to avoid blocking the event loop on gspread's network calls
            await asyncio.to_thread(self._append_sync, sheet_id, tab_name, row_data, app_state)
            logger.info("sheets_row_appended", tab=tab_name)
        except Exception as exc:
            logger.error(
                "sheets_append_failed",
                error_type=type(exc).__name__,
                tab=tab_name,
            )
            raise

    def _append_sync(self, sheet_id: str, tab_name: str, row_data: list[Any], app_state=None) -> None:
        """
        Internal sync method for gspread calls. Performs network IO, 
        must be called via asyncio.to_thread.
        """
        # Pull client from state if available (best)
        client = getattr(app_state, "sheets", None) if app_state else None
        if not client:
            client = get_sheets_client()
        
        spreadsheet = client.open_by_key(sheet_id)

        try:
            worksheet = spreadsheet.worksheet(tab_name)
        except Exception:
            # Create if missing
            worksheet = spreadsheet.add_worksheet(title=tab_name, rows=1000, cols=len(_HEADER))
            # Insert header as the first row
            worksheet.insert_row(_HEADER, 1)
        
        # Append the new row data
        worksheet.append_row(row_data)


sheets_tools = SheetsTools()