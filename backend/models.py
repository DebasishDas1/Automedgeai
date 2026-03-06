from sqlalchemy import Column, String, Text, DateTime, ForeignKey, UUID
from sqlalchemy.sql import func
import uuid
from .db import Base

class Lead(Base):
    __tablename__ = "leads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    phone = Column(String)
    email = Column(String)
    source = Column(String)  # google|angi|phone|web
    vertical = Column(String)  # hvac|roofing|plumbing|pest
    stage = Column(String, default="new")  # new|contacted|quoted|booked|done
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    user_id = Column(String, nullable=False)  # Firebase UID

class Job(Base):
    __tablename__ = "jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.id"))
    tech_name = Column(String)
    scheduled = Column(DateTime(timezone=True))
    status = Column(String)
    notes = Column(Text)

class Booking(Base):
    __tablename__ = "bookings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String)
    email = Column(String)
    vertical = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
