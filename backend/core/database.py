import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey,
    Integer, String, Text, select,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.ext.asyncio import (
    AsyncSession, async_sessionmaker, create_async_engine,
)
from sqlalchemy.orm import declarative_base

from core.config import settings

# ── Engine ────────────────────────────────────────────────────────────────────

engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=20,
    max_overflow=10,
    pool_timeout=30,
    pool_pre_ping=True,
    pool_recycle=1800,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession,
)

Base = declarative_base()


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ── Models ────────────────────────────────────────────────────────────────────

class Lead(Base):
    __tablename__ = "leads"

    id         = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name       = Column(String,  nullable=True)
    email      = Column(String,  nullable=True)
    phone      = Column(String,  nullable=True)
    issue      = Column(Text,    nullable=True)
    address    = Column(String,  nullable=True)
    vertical   = Column(String,  nullable=False)
    score      = Column(String,  nullable=True)   # "hot" | "warm" | "cold"
    summary    = Column(Text,    nullable=True)
    appt_at    = Column(DateTime(timezone=True), nullable=True)
    session_id = Column(String,  nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), default=_now)


class Job(Base):
    __tablename__ = "jobs"

    id           = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lead_id      = Column(PG_UUID(as_uuid=True), ForeignKey("leads.id"))
    tech_name    = Column(String,  nullable=True)
    tech_phone   = Column(String,  nullable=True)
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    status       = Column(String,  default="pending")
    notes        = Column(Text,    nullable=True)
    created_at   = Column(DateTime(timezone=True), default=_now)


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id          = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id  = Column(String, unique=True, nullable=False, index=True)
    vertical    = Column(String, nullable=False, default="hvac")
    state       = Column(JSONB,  nullable=False, default=dict)
    form_data   = Column(JSONB,  nullable=True,  default=None)
    is_complete = Column(Boolean, default=False)
    created_at  = Column(DateTime(timezone=True), default=_now)
    updated_at  = Column(DateTime(timezone=True), default=_now)


class Booking(Base):
    """Demo / onboarding booking from the marketing site."""
    __tablename__ = "bookings"

    id         = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name       = Column(String, nullable=False)
    email      = Column(String, nullable=False)
    business   = Column(String, nullable=False)
    vertical   = Column(String, nullable=False)
    team_size  = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=_now)


class WorkflowEvent(Base):
    """
    One row per workflow step for a lead.
    Consumed by workflow_trigger_tools SSE stream for the dashboard.
    Matches WorkflowEventResponse in models/workflow.py exactly.
    """
    __tablename__ = "workflow_events"

    id            = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lead_id       = Column(PG_UUID(as_uuid=True), ForeignKey("leads.id"), nullable=False, index=True)
    step          = Column(Integer, nullable=False)
    label         = Column(String,  nullable=False)
    status        = Column(String,  nullable=False, default="active")  # active | done | error
    timestamp_str = Column(String,  nullable=True)
    created_at    = Column(DateTime(timezone=True), default=_now)


# ── DB helpers ────────────────────────────────────────────────────────────────

async def get_db():
    """FastAPI dependency — yields a session, closes on exit."""
    async with AsyncSessionLocal() as session:
        yield session


@asynccontextmanager
async def get_db_context():
    """Async context manager for use outside FastAPI dependency injection."""
    async with AsyncSessionLocal() as session:
        yield session


async def init_db() -> None:
    """Create all tables that don't exist. Safe to call on every startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


__all__ = [
    "engine",
    "Base",
    "Lead",
    "Job",
    "ChatSession",
    "Booking",
    "WorkflowEvent",
    "get_db",
    "get_db_context",
    "init_db",
    "select",
]