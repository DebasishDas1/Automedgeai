# core/lifespan.py
import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI
from core.config import settings
from core.database import init_db, engine
from workflows.registry import registry

logger = structlog.get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup/shutdown managed by FastAPI lifespan.
    Initializes SDK clients (Retell, Twilio, Resend, HubSpot, Sheets) and
    warms up LangGraph graph caches.
    """
    logger.info("startup_begin", environment=settings.ENVIRONMENT)
    try:
        # Lazy imports to avoid circular dependencies and keep startup clean
        from retell import Retell
        from core.firebase import init_firebase
        from twilio.rest import Client as TwilioClient
        import resend
        from hubspot import HubSpot
        from core.sheets import get_sheets_client

        # 1. DB & Graph Warming
        await init_db()
        await registry.initialize()
        init_firebase()

        # 2. Retell (Mandatory)
        if not settings.RETELL_API_KEY:
            raise RuntimeError("RETELL_API_KEY is not set.")
        app.state.retell = Retell(api_key=settings.RETELL_API_KEY)

        # 3. Twilio (Optional)
        if settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN:
            app.state.twilio = TwilioClient(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        else:
            app.state.twilio = None
            logger.warning("startup_twilio_skipped", reason="missing_credentials")

        # 4. Resend (Optional)
        if settings.RESEND_API_KEY:
            resend.api_key = settings.RESEND_API_KEY
            app.state.resend = resend.Emails
        else:
            app.state.resend = None
            logger.warning("startup_resend_skipped", reason="missing_api_key")

        # 5. HubSpot (Optional)
        if settings.HUBSPOT_ACCESS_TOKEN:
            app.state.hubspot = HubSpot(access_token=settings.HUBSPOT_ACCESS_TOKEN)
        else:
            app.state.hubspot = None
            logger.warning("startup_hubspot_skipped", reason="missing_token")

        # 6. Sheets (Optional)
        try:
            app.state.sheets = get_sheets_client()
        except Exception as exc:
            app.state.sheets = None
            logger.warning(
                "startup_sheets_failed",
                error_type=type(exc).__name__,
            )

        logger.info("startup_complete")
        yield
    except Exception as exc:
        logger.error(
            "startup_failed",
            error_type=type(exc).__name__,
        )
        raise
    finally:
        logger.info("shutdown_begin")
        try:
            await engine.dispose()
        finally:
            logger.info("shutdown_complete")
