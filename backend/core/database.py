import os
import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Text, UUID
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
import uuid
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

Base = declarative_base()

class Lead(Base):
    __tablename__ = "leads"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    source = Column(String, nullable=False)      # google|angi|phone|web
    vertical = Column(String, nullable=False)    # hvac|roofing|plumbing|pest
    issue = Column(Text, nullable=True)
    city = Column(String, nullable=True)
    stage = Column(String, default="new")        # new|contacted|quoted|booked|done
    urgency = Column(String, default="normal")   # emergency|urgent|normal
    sms_sent = Column(Boolean, default=False)
    tech_notified = Column(Boolean, default=False)
    booked_at = Column(DateTime, nullable=True)
    review_sent = Column(Boolean, default=False)
    sheet_row = Column(Integer, nullable=True)
    user_id = Column(String, nullable=False)      # Firebase UID
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class Job(Base):
    __tablename__ = "jobs"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lead_id = Column(PG_UUID(as_uuid=True), ForeignKey("leads.id"))
    tech_name = Column(String, nullable=True)
    tech_phone = Column(String, nullable=True)
    scheduled_at = Column(DateTime, nullable=True)
    status = Column(String, default="pending")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Booking(Base):
    __tablename__ = "bookings"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    business = Column(String, nullable=False)
    vertical = Column(String, nullable=False)
    team_size = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class WorkflowEvent(Base):
    __tablename__ = "workflow_events"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lead_id = Column(PG_UUID(as_uuid=True), ForeignKey("leads.id"))
    step = Column(Integer, nullable=False)
    label = Column(String, nullable=False)
    status = Column(String, nullable=False)      # active|done|error
    timestamp_str = Column(String, nullable=True) # "47s" "1m 12s"
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
