"""FastAPI app factory for the Capital Markets Teams-agent demo backend."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.infra.settings import get_settings
from app.infra.telemetry import setup_telemetry
from app.routers import demo, health

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_telemetry()
    yield


app = FastAPI(
    title="Capital Markets Teams Agent — Option A + B Demo",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(demo.router, prefix="/api", tags=["demo"])
