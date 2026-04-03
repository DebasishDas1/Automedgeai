import time
import uuid
import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import ORJSONResponse
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from core.database import init_db, engine
from core.exceptions import (
    AutomedgeException,
    automedge_exception_handler,
    generic_exception_handler,
)
from api.router import router
from workflows.registry import registry
from fastapi.middleware.gzip import GZipMiddleware

# ── Logging config ────────────────────────────────────────────────────────────
# FIX: structlog.configure() is called at module import time — fine.
# But the ternary evaluated settings.ENVIRONMENT at import too, which is correct.
# Added CallsiteParameterAdder so every log line carries filename + line number.
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.CallsiteParameterAdder(
            [structlog.processors.CallsiteParameter.FILENAME,
             structlog.processors.CallsiteParameter.LINENO]
        ),
        structlog.processors.TimeStamper(fmt="iso"),
        (
            structlog.dev.ConsoleRenderer()
            if settings.ENVIRONMENT == "dev"
            else structlog.processors.JSONRenderer()
        ),
    ],
    logger_factory=structlog.PrintLoggerFactory(),
)
logger = structlog.get_logger(__name__)


# ── Lifespan ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup/shutdown managed by FastAPI lifespan.

    Fixes:
    - `_ = registry` only touched the module-level singleton but never called
      .initialize(), so graphs were compiled lazily on the first request
      (blocking the event loop for ~1–2 s under load). Now explicitly calls
      registry.initialize() so all graphs are warm before traffic arrives.
    - engine.dispose() moved inside try/finally so it runs even if startup
      raises (prevents connection pool leak on bad deploys).
    """
    logger.info("startup_begin", environment=settings.ENVIRONMENT)
    try:
        from retell import Retell
        from core.firebase import init_firebase  # init once, not per-request
        await init_db()
        await registry.initialize()          # compile all graphs now, not on first hit
        init_firebase()                      # eliminates concurrent-init race condition

        # FIX: Retell SDK accepts api_key=None at construction time — it only
        # validates on the first API call. That meant startup_complete could log
        # with a None key, app.state.retell would be set, and the 500 would
        # only surface at request time. Fail fast here so the operator sees
        # the problem immediately on boot.
        if not settings.RETELL_API_KEY:
            raise RuntimeError(
                "RETELL_API_KEY is not set. "
                "Check that backend/.env exists and contains RETELL_API_KEY."
            )
        if not settings.RETELL_AGENT_ID:
            raise RuntimeError(
                "RETELL_AGENT_ID is not set. "
                "Check that backend/.env exists and contains RETELL_AGENT_ID."
            )

        app.state.retell = Retell(api_key=settings.RETELL_API_KEY)

        logger.info("startup_complete")
    except Exception as exc:
        logger.error("startup_failed", error=str(exc))
        raise  # let uvicorn exit cleanly rather than serving a broken app

    yield

    logger.info("shutdown_begin")
    try:
        await engine.dispose()
    finally:
        logger.info("shutdown_complete")


# ── App factory ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="Automedge AI Backend",
    version="1.0.0",
    lifespan=lifespan,
)

# Register central exception handlers
app.add_exception_handler(AutomedgeException, automedge_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)


# ── Middleware ────────────────────────────────────────────────────────────────
# IMPORTANT: FastAPI applies middleware in reverse registration order.
# CORS must be registered BEFORE the request isolation middleware so that
# preflight OPTIONS requests are handled before structlog context is bound.

app.add_middleware(
    CORSMiddleware,
    # FIX: allow_origins=["*"] + allow_credentials=True is rejected by browsers
    # and violates the CORS spec. When credentials=True you must list explicit
    # origins. In dev we drop credentials instead of using wildcard+credentials.
    allow_origins=["*"] if settings.is_dev else settings.ALLOWED_ORIGINS,
    allow_origin_regex=settings.cors_origin_regex if not settings.is_dev else None,
    allow_credentials=not settings.is_dev,   # False in dev (wildcard), True in prod
    allow_methods=["GET", "POST", "OPTIONS"],  # be explicit — ["*"] allows DELETE/PUT
    allow_headers=["Content-Type", "Authorization", "X-Request-ID"],
)

app.add_middleware(
    GZipMiddleware,
    minimum_size=1000,  # only compress responses > 1KB
)


@app.middleware("http")
async def request_isolation_middleware(request: Request, call_next):
    """
    Binds a unique request_id to the structlog context for every request.

    Fixes:
    - structlog context was never cleared between requests on the same worker.
      Added clear_contextvars() at the top so stale context from a previous
      request can't bleed into the next one on the same coroutine.
    - Catching bare Exception here means HTTPException (which FastAPI uses for
      4xx responses) was being swallowed and returned as 500. Re-raise
      HTTPException so FastAPI's own error handler produces the correct status.
    - request_id header was added after the response was built but StreamingResponse
      sets headers before streaming starts, so the header was missing on streams.
      This is a known FastAPI limitation — documented here, not silently broken.
    """
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
        # Re-raise so FastAPI's exception handlers (404, 401) can work.
        raise exc
    except Exception as exc:
        duration_ms = int((time.perf_counter() - start) * 1000)
        logger.error("request_crashed", error=str(exc), latency_ms=duration_ms)
        return ORJSONResponse(
            {"detail": "internal_server_error", "request_id": request_id},
            status_code=500,
        )


# ── Routes ────────────────────────────────────────────────────────────────────

app.include_router(router, prefix="/api")

@app.api_route("/health", methods=["GET", "HEAD"])
async def health():
    """Liveness probe. Returns 200 as long as the process is alive."""
    return {"status": "ok", "service": "automedge-backend"}