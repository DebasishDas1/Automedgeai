from __future__ import annotations
import json
from typing import Optional, List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # -------------------------
    # Environment
    # -------------------------
    ENVIRONMENT: str = "dev"  # dev | prod

    @property
    def is_dev(self) -> bool:
        return self.ENVIRONMENT == "dev"

    # -------------------------
    # Database
    # -------------------------
    DATABASE_URL: Optional[str] = None

    # -------------------------
    # Firebase
    # -------------------------
    FIREBASE_CREDENTIALS_JSON: Optional[str] = None

    # -------------------------
    # Google Sheets
    # -------------------------
    SHEETS_CREDENTIALS_JSON: Optional[str] = None
    HVAC_SHEET_ID: Optional[str] = None
    ROOFING_SHEET_ID: Optional[str] = None
    PLUMBING_SHEET_ID: Optional[str] = None
    PEST_SHEET_ID: Optional[str] = None

    # -------------------------
    # Twilio
    # -------------------------
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_FROM_NUMBER: Optional[str] = None

    # -------------------------
    # Email (Resend)
    # -------------------------
    RESEND_API_KEY: Optional[str] = None
    EMAIL_FROM: str = "onboarding@resend.dev"

    # -------------------------
    # LLM
    # -------------------------
    GROQ_API_KEY: Optional[str] = None
    MAX_TOKEN: int = 1024

    # -------------------------
    # CORS (Fixed Properly)
    # -------------------------
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_origins(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)  # ✅ proper JSON parsing
            except Exception:
                return [i.strip() for i in v.split(",") if i.strip()]
        return v

    @property
    def cors_origin_regex(self) -> str:
        if self.is_dev:
            return r"http://.*\.localhost:3000"
        return r"https://.*\.vercel\.app"

    # -------------------------
    # Ollama (dev only)
    # -------------------------
    OLLAMA_BASE_URL: str = "http://localhost:11434/v1"
    OLLAMA_MODEL: str = "qwen3:1.7b"

    # -------------------------
    # Business contact
    # -------------------------
    BUSINESS_PHONE: str = "+1-555-000-0000"
    TEAM_EMAIL: str = "team@automedge.com"

    # -------------------------
    # Helpers
    # -------------------------
    def sheets_credentials_dict(self) -> dict | None:
        if not self.SHEETS_CREDENTIALS_JSON:
            return None
        return json.loads(self.SHEETS_CREDENTIALS_JSON)

    def firebase_credentials_dict(self) -> dict | None:
        if not self.FIREBASE_CREDENTIALS_JSON:
            return None
        return json.loads(self.FIREBASE_CREDENTIALS_JSON)


settings = Settings()