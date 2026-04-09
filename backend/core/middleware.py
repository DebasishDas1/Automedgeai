# core/middleware.py
import time
import uuid
import structlog
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import ORJSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from core.config import settings

logger = structlog.get_logger(__name__)

def setup_middleware(app: FastAPI):
    """
    Applies CORS, GZip, and custom request isolation middleware.
    """
    # 1. CORS
    # Use explicit allow list even in dev, never use wildcard "*" with allow_credentials
    cors_origins = ["http://localhost:3000", "http://localhost:3001"] if settings.is_dev else settings.ALLOWED_ORIGINS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_origin_regex=settings.cors_origin_regex if not settings.is_dev else None,
        allow_credentials=True if settings.is_dev else False,
        allow_methods=["GET", "POST", "OPTIONS", "PUT", "PATCH", "DELETE"],
        allow_headers=["Content-Type", "Authorization", "X-Request-ID"],
    )

    # 2. GZip
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # 3. Request Isolation & Structlog Context
    @app.middleware("http")
    async def request_isolation_middleware(request: Request, call_next):
        structlog.contextvars.clear_contextvars()
        request_id = str(uuid.uuid4())
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
        )

        start = time.perf_counter()
        try:
            response = await call_next(request)
            duration_ms = int((time.perf_counter() - start) * 1000)
            logger.info("request_finished", status=response.status_code, latency_ms=duration_ms)
            response.headers["X-Request-ID"] = request_id
            return response

        except HTTPException as exc:
            # Re-raise so FastAPI exception handlers (404, 401) can perform their logic
            raise exc
        except Exception as exc:
            duration_ms = int((time.perf_counter() - start) * 1000)
            # Log exception type but not full message to prevent logging sensitive data
            logger.error(
                "request_crashed",
                error_type=type(exc).__name__,
                latency_ms=duration_ms,
            )
            return ORJSONResponse(
                {"detail": "internal_server_error", "request_id": request_id},
                status_code=500,
            )
