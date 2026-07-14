from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from structlog import get_logger

from app.application.services import analytics as analytics_service
from app.infrastructure.database import get_db
from app.presentation.dependencies import get_current_user

logger = get_logger()
router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/dashboard")
async def get_dashboard(
    user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> dict:
    return await analytics_service.get_dashboard(session, user["id"])


@router.post("/weekly-report")
async def generate_weekly_report(
    user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> dict:
    return await analytics_service.generate_weekly_report(session, user["id"])


@router.get("/reports")
async def list_reports(
    user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> list[dict]:
    return await analytics_service.list_reports(session, user["id"])
