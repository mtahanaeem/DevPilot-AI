from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from structlog import get_logger

from app.infrastructure.database.models.notification import NotificationModel

logger = get_logger()


async def list_notifications(session: AsyncSession, user_id: Any) -> list[dict]:
    result = await session.execute(
        select(NotificationModel)
        .where(NotificationModel.user_id == user_id)
        .order_by(NotificationModel.created_at.desc())
        .limit(50)
    )
    notifications = result.scalars().all()
    return [
        {
            "id": str(n.id),
            "event_type": n.event_type,
            "channel": n.channel,
            "sent_at": n.sent_at.isoformat() if n.sent_at else None,
            "status": n.status,
            "created_at": n.created_at.isoformat(),
        }
        for n in notifications
    ]


async def create_notification(
    session: AsyncSession, user_id: Any, event_type: str, channel: str = "in_app"
) -> dict:
    notification = NotificationModel(
        user_id=user_id,
        event_type=event_type,
        channel=channel,
        status="pending",
    )
    session.add(notification)
    await session.commit()
    await session.refresh(notification)
    return {
        "id": str(notification.id),
        "event_type": notification.event_type,
        "channel": notification.channel,
        "status": notification.status,
        "created_at": notification.created_at.isoformat(),
    }


async def mark_read(session: AsyncSession, notification_id: Any, user_id: Any) -> dict:
    result = await session.execute(
        select(NotificationModel).where(
            NotificationModel.id == notification_id,
            NotificationModel.user_id == user_id,
        )
    )
    notification = result.scalar_one_or_none()
    if notification is None:
        raise ValueError(f"Notification {notification_id} not found")

    notification.status = "sent"
    await session.commit()
    return {"id": str(notification.id), "status": "sent"}


async def mark_all_read(session: AsyncSession, user_id: Any) -> dict:
    result = await session.execute(
        select(NotificationModel).where(
            NotificationModel.user_id == user_id,
            NotificationModel.status == "pending",
        )
    )
    notifications = result.scalars().all()
    for n in notifications:
        n.status = "sent"
    await session.commit()
    return {"updated": len(notifications)}
