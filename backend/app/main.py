from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from structlog import get_logger

from app.core.config import settings
from app.core.logging import setup_logging
from app.core.middleware import RequestIDMiddleware, RequestTimingMiddleware
from app.presentation.routers import (
    analytics, auth, documents, github_webhooks, health, interview,
    learning, notifications, opensource, portfolio, repositories, resume, skills, social,
)

logger = get_logger()


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    setup_logging()
    logger.info("DevPilot AI backend starting", version="1.0.0")
    yield
    logger.info("DevPilot AI backend shutting down")


app = FastAPI(
    title="DevPilot AI API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:3000", "http://localhost:80"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(RequestTimingMiddleware)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(github_webhooks.router)
app.include_router(portfolio.router)
app.include_router(repositories.router)
app.include_router(resume.router)
app.include_router(skills.router)
app.include_router(learning.router)
app.include_router(interview.router)
app.include_router(opensource.router)
app.include_router(social.router)
app.include_router(analytics.router)
app.include_router(notifications.router)
