import time
import uuid
import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import ORJSONResponse
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from core.database import init_db, engine
from api.router import router
from workflows.registry import registry

# Synchronous logging config (safe for startup)
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer() if settings.ENVIRONMENT != "dev" else structlog.dev.ConsoleRenderer()
    ],
    logger_factory=structlog.PrintLoggerFactory(),
)
logger = structlog.get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Lock-guarded initialization during startup
    logger.info("startup_init")
    await init_db()
    
    # Force Graph Registry singleton initialization inside the event loop
    _ = registry 
    
    yield
    
    logger.info("shutdown_cleanup")
    await engine.dispose()

app = FastAPI(
    title="Automedge AI Backend",
    lifespan=lifespan,
    default_response_class=ORJSONResponse,
)

@app.middleware("http")
async def request_isolation_middleware(request: Request, call_next):
    # Context propagation with absolute request isolation
    request_id = str(uuid.uuid4())
    structlog.contextvars.bind_contextvars(request_id=request_id)
    
    start = time.perf_counter()
    try:
        response = await call_next(request)
        duration = int((time.perf_counter() - start) * 1000)
        logger.info("request_finished", status=response.status_code, latency_ms=duration)
        response.headers["X-Request-ID"] = request_id
        return response
    except Exception as e:
        logger.error("request_crashed", error=str(e))
        return ORJSONResponse({"detail": "critical_internal_error"}, status_code=500)


if settings.is_dev:
    allow_origins = ["*"]
    allow_origin_regex = r"http://.*\.localhost:3000"
else:
    allow_origins = settings.ALLOWED_ORIGINS
    allow_origin_regex = r"https://.*\.vercel\.app"

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_origin_regex=allow_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")

@app.api_route("/health", methods=["GET", "HEAD"])
async def health():
    return {
        "status": "ok",
        "service": "automedge-backend"
    }