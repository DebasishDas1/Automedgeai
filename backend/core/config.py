import json
from typing import List, Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )

    # Database
    DATABASE_URL: Optional[str] = None

    # Firebase
    FIREBASE_CREDENTIALS_JSON: Optional[str] = None

    # Google Sheets
    SHEETS_CREDENTIALS_JSON: Optional[str] = None
    HVAC_SHEET_ID: Optional[str] = None
    ROOFING_SHEET_ID: Optional[str] = None
    PLUMBING_SHEET_ID: Optional[str] = None
    PEST_SHEET_ID: Optional[str] = None

    # Twilio
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_FROM_NUMBER: Optional[str] = None

    # Email
    RESEND_API_KEY: Optional[str] = None
    EMAIL_FROM: Optional[str] = None

    # LLM
    GROQ_API_KEY: Optional[str] = None

    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]

    # Limits
    MAX_TOKEN: int = 1024

    # Environment
    ENVIRONMENT: str = "dev"

    # Ollama
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3"

    # ---------- Validators ----------

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def split_origins(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v

    # ---------- Helpers ----------

    def sheets_credentials_dict(self):
        if not self.SHEETS_CREDENTIALS_JSON:
            return None
        return json.loads(self.SHEETS_CREDENTIALS_JSON)

    def firebase_credentials_dict(self):
        if not self.FIREBASE_CREDENTIALS_JSON:
            return None
        return json.loads(self.FIREBASE_CREDENTIALS_JSON)


settings = Settings()