import gspread
from core.config import settings
from google.oauth2.service_account import Credentials
import logging

logger = logging.getLogger(__name__)

class SheetsTool:
    def __init__(self):
        self.scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        self._client = None

    @property
    def client(self):
        if self._client is None:
            try:
                creds = Credentials.from_service_account_file(
                    settings.SHEETS_CREDENTIALS_PATH,
                    scopes=self.scopes
                )
                self._client = gspread.authorize(creds)
            except Exception as e:
                logger.error(f"Failed to authorize Google Sheets: {e}")
                raise
        return self._client

    def append_row(self, vertical: str, row_data: list) -> int | None:
        """
        Appends a row to the specified vertical's sheet.
        Returns the row index if successful.
        """
        sheet_id_map = {
            "hvac": settings.HVAC_SHEET_ID,
            "roofing": settings.ROOFING_SHEET_ID,
            "plumbing": settings.PLUMBING_SHEET_ID,
            "pest_control": settings.PEST_SHEET_ID
        }
        
        sheet_id = sheet_id_map.get(vertical)
        if not sheet_id:
            logger.error(f"No sheet ID found for vertical: {vertical}")
            return None

        try:
            sh = self.client.open_by_key(sheet_id)
            worksheet = sh.get_worksheet(0)
            response = worksheet.append_row(row_data)
            # Row index is in updates -> updatedRange
            # "Sheet1!A10:E10" -> 10
            updated_range = response.get('updates', {}).get('updatedRange', '')
            if '!' in updated_range:
                cell_range = updated_range.split('!')[1]
                # Filter out alphabets to get the row number
                row_str = ''.join(filter(str.isdigit, cell_range.split(':')[0]))
                return int(row_str) if row_str else None
            return None
        except Exception as e:
            logger.error(f"Failed to append row to Google Sheets: {e}")
            return None

sheets_tool = SheetsTool()
