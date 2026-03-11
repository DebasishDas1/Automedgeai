import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
import uuid
from sqlalchemy.ext.asyncio import async_sessionmaker
from contextlib import asynccontextmanager
from core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    connect_args={"ssl": True}
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False
)
Base = declarative_base()


class Lead(Base):
    __tablename__ = "leads"

    id            = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name          = Column(String, nullable=False)
    phone         = Column(String, nullable=True)
    email         = Column(String, nullable=True)
    source        = Column(String, nullable=False)       # google|angi|phone|web|chat
    vertical      = Column(String, nullable=False)       # hvac|roofing|plumbing|pest_control
    issue         = Column(Text, nullable=True)
    city          = Column(String, nullable=True)
    stage         = Column(String, default="new")        # new|contacted|quoted|booked|done
    urgency       = Column(String, default="normal")     # emergency|urgent|normal
    score         = Column(String, nullable=True)        # hot|warm|cold
    score_reason  = Column(Text, nullable=True)
    sms_sent      = Column(Boolean, default=False)
    tech_notified = Column(Boolean, default=False)
    booked_at     = Column(DateTime, nullable=True)
    review_sent   = Column(Boolean, default=False)
    sheet_row     = Column(Integer, nullable=True)
    session_id    = Column(String, nullable=True)        # linked chat session
    user_id       = Column(String, nullable=False)       # Firebase UID
    created_at    = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at    = Column(DateTime, default=datetime.datetime.utcnow,
                           onupdate=datetime.datetime.utcnow)


class Job(Base):
    __tablename__ = "jobs"

    id           = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lead_id      = Column(PG_UUID(as_uuid=True), ForeignKey("leads.id"))
    tech_name    = Column(String, nullable=True)
    tech_phone   = Column(String, nullable=True)
    scheduled_at = Column(DateTime, nullable=True)
    status       = Column(String, default="pending")
    notes        = Column(Text, nullable=True)
    created_at   = Column(DateTime, default=datetime.datetime.utcnow)


class Booking(Base):
    __tablename__ = "bookings"

    id         = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name       = Column(String, nullable=False)
    email      = Column(String, nullable=False)
    business   = Column(String, nullable=False)
    vertical   = Column(String, nullable=False)
    team_size  = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class WorkflowEvent(Base):
    __tablename__ = "workflow_events"

    id            = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lead_id       = Column(PG_UUID(as_uuid=True), ForeignKey("leads.id"))
    step          = Column(Integer, nullable=False)
    label         = Column(String, nullable=False)
    status        = Column(String, nullable=False)       # active|done|error
    timestamp_str = Column(String, nullable=True)        # "47s" "1m 12s"
    created_at    = Column(DateTime, default=datetime.datetime.utcnow)


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id          = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id  = Column(String, unique=True, nullable=False)
    vertical    = Column(String, nullable=False, default="hvac")
    state       = Column(JSONB, nullable=False)
    score       = Column(String, nullable=True)
    sheet_row   = Column(Integer, nullable=True)
    sheet_tab   = Column(String, nullable=True)
    email_sent  = Column(Boolean, default=False)
    appt_booked = Column(Boolean, default=False)
    is_complete = Column(Boolean, default=False)
    created_at  = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at  = Column(DateTime, default=datetime.datetime.utcnow,
                         onupdate=datetime.datetime.utcnow)


async def get_db():
    """FastAPI dependency — yields AsyncSession for one request."""
    async with AsyncSessionLocal() as session:
        yield session


@asynccontextmanager
async def get_db_context():
    """Context manager for background tasks that need a session outside a request."""
    async with AsyncSessionLocal() as session:
        yield session


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)