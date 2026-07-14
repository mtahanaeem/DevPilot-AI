from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from structlog import get_logger

from app.core.config import settings
from app.infrastructure.database import get_db

logger = get_logger()
router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> dict:
    return {
        "status": "healthy",
        "version": "1.0.0",
        "llm_provider": settings.LLM_PROVIDER,
    }


@router.get("/health/db")
async def db_health(session: AsyncSession = Depends(get_db)) -> dict:
    try:
        await session.execute(text("SELECT 1"))
        return {"status": "healthy", "service": "postgres"}
    except Exception as exc:
        logger.error("db health check failed", exc_info=exc)
        return {"status": "unhealthy", "service": "postgres", "error": str(exc)}
