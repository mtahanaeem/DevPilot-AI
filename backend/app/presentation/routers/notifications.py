from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from structlog import get_logger

from app.application.services import notifications as notification_service
from app.infrastructure.database import get_db
from app.presentation.dependencies import get_current_user

logger = get_logger()
router = APIRouter(prefix="/notifications", tags=["notifications"])


class NotificationOut(BaseModel):
    id: str
    event_type: str
    channel: str
    sent_at: str | None
    status: str
    created_at: str


@router.get("")
async def list_notifications(
    user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> list[NotificationOut]:
    return await notification_service.list_notifications(session, user["id"])


@router.post("/{notification_id}/read")
async def mark_read(
    notification_id: str,
    user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> dict:
    try:
        return await notification_service.mark_read(session, notification_id, user["id"])
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/mark-all-read")
async def mark_all_read(
    user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> dict:
    return await notification_service.mark_all_read(session, user["id"])
