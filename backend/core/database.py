import datetime
import uuid
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from contextlib import asynccontextmanager
from core.config import settings

# Thread-safe async engine with tuned connection pooling for high concurrency
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=20,           # Matches expected concurrent request volume
    max_overflow=10,        # Flexible burst capacity
    pool_timeout=30,        # Prevents request hangs
    pool_pre_ping=True,      # Resilient to database restarts
    pool_recycle=1800,      # Refresh connections
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession
)

Base = declarative_base()

class Lead(Base):
    __tablename__ = "leads"
    id         = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name       = Column(String,   nullable=True)
    email      = Column(String,   nullable=True)
    phone      = Column(String,   nullable=True)
    issue      = Column(Text,     nullable=True)
    address    = Column(String,   nullable=True)
    vertical   = Column(String,   nullable=False)
    appt_at    = Column(DateTime, nullable=True)
    session_id = Column(String,   nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

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

class ChatSession(Base):
    __tablename__ = "chat_sessions"
    id          = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id  = Column(String, unique=True, nullable=False, index=True)
    vertical    = Column(String, nullable=False, default="hvac")
    state       = Column(JSONB, nullable=False)
    is_complete = Column(Boolean, default=False)
    created_at  = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at  = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

@asynccontextmanager
async def get_db_context():
    async with AsyncSessionLocal() as session:
        yield session

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)