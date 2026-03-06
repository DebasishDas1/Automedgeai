from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.router import router
from core.config import settings

app = FastAPI(title="automedge API", version="1.0.0")

app.add_middleware(CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(router, prefix="/api/v1")