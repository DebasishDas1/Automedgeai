from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
from dotenv import load_dotenv

load_dotenv()

from .workflow import router as workflow_router

app = FastAPI(title="Automedge API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://automedge.com", "http://localhost:3000"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

from .auth import verify_firebase_token
from .models import Lead
from .db import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

app.include_router(workflow_router)

@app.get("/healthz")
async def health_check():
    return {"status": "alive"}

@app.post("/api/leads")
async def create_lead(
    lead_data: dict, 
    db: AsyncSession = Depends(get_db), 
    user: dict = Depends(verify_firebase_token)
):
    new_lead = Lead(
        name=lead_data["name"],
        phone=lead_data.get("phone"),
        email=lead_data.get("email"),
        source=lead_data.get("source"),
        vertical=lead_data.get("vertical"),
        user_id=user["uid"]
    )
    db.add(new_lead)
    await db.commit()
    await db.refresh(new_lead)
    return new_lead

@app.get("/api/leads")
async def list_leads(
    db: AsyncSession = Depends(get_db), 
    user: dict = Depends(verify_firebase_token)
):
    result = await db.execute(
        select(Lead).where(Lead.user_id == user["uid"])
    )
    leads = result.scalars().all()
    return leads

@app.post("/api/book-demo")
async def book_demo(
    booking_data: dict, 
    db: AsyncSession = Depends(get_db)
):
    # Public endpoint to book a demo
    return {"message": "Demo booked successfully"}
