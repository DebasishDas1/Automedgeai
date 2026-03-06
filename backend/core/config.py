from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Neon
    DATABASE_URL: str

    # Firebase
    FIREBASE_CREDENTIALS_PATH: str

    # Google Sheets
    SHEETS_CREDENTIALS_PATH: str
    HVAC_SHEET_ID: str
    ROOFING_SHEET_ID: str
    PLUMBING_SHEET_ID: str
    PEST_SHEET_ID: str

    # Twilio
    TWILIO_ACCOUNT_SID: str
    TWILIO_AUTH_TOKEN: str
    TWILIO_FROM_NUMBER: str

    # Resend
    RESEND_API_KEY: str

    # OpenAI (LangGraph)
    OPENAI_API_KEY: str

    # CORS
    ALLOWED_ORIGINS: list[str] = ["https://automedge.com", "http://localhost:3000"]

    class Config:
        env_file = ".env"

settings = Settings()