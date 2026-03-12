from __future__ import annotations
import json
from typing import Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database
    DATABASE_URL: Optional[str] = None

    # Firebase
    FIREBASE_CREDENTIALS_JSON: Optional[str] = None

    # Google Sheets
    SHEETS_CREDENTIALS_JSON: Optional[str] = None
    HVAC_SHEET_ID:    Optional[str] = None
    ROOFING_SHEET_ID: Optional[str] = None
    PLUMBING_SHEET_ID: Optional[str] = None
    PEST_SHEET_ID:    Optional[str] = None

    # Twilio
    TWILIO_ACCOUNT_SID:  Optional[str] = None
    TWILIO_AUTH_TOKEN:   Optional[str] = None
    TWILIO_FROM_NUMBER:  Optional[str] = None

    # Email (Resend)
    RESEND_API_KEY: Optional[str] = None
    EMAIL_FROM:     str = "onboarding@resend.dev"

    # LLM
    GROQ_API_KEY:   Optional[str] = None
    MAX_TOKEN:      int = 1024

    # CORS — accepts comma string ("a.com,b.com") or JSON array
    ALLOWED_ORIGINS: str | list[str] = "http://localhost:3000"

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def split_origins(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",") if i.strip()]
        return v

    ENVIRONMENT: str = "dev"

    # Ollama (development only)
    OLLAMA_BASE_URL: str = "http://localhost:11434/v1"
    OLLAMA_MODEL:    str = "qwen3:1.7b"

    # Business contact
    BUSINESS_PHONE: str = "+1-555-000-0000"
    TEAM_EMAIL:     str = "team@automedge.com"

    # ── Helpers ───────────────────────────────────────────────────────────────

    def sheets_credentials_dict(self) -> dict | None:
        if not self.SHEETS_CREDENTIALS_JSON:
            return None
        return json.loads(self.SHEETS_CREDENTIALS_JSON)

    def firebase_credentials_dict(self) -> dict | None:
        if not self.FIREBASE_CREDENTIALS_JSON:
            return None
        return json.loads(self.FIREBASE_CREDENTIALS_JSON)


settings = Settings()