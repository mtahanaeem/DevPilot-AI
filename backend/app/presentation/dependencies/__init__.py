from __future__ import annotations

from fastapi import Depends, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from structlog import get_logger

from app.core.config import settings
from app.core.exceptions import UnauthorizedError
from app.core.security import decode_access_token
from app.infrastructure.database import get_db as _get_db
from app.infrastructure.database.models.user import UserModel

logger = get_logger()


async def get_db() -> AsyncSession:
    async for session in _get_db():
        yield session


async def _resolve_n8n_user(session: AsyncSession) -> dict:
    result = await session.execute(
        select(UserModel).where(UserModel.oauth_token == settings.GITHUB_PAT)
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise UnauthorizedError("No user found for the configured GITHUB_PAT")
    return {
        "id": str(user.id),
        "github_username": user.github_username,
        "pat": settings.GITHUB_PAT,
    }


async def get_current_user(
    authorization: str = Header(""),
    session: AsyncSession = Depends(get_db),
) -> dict:
    if not authorization.startswith("Bearer "):
        raise UnauthorizedError("Missing or invalid Authorization header")
    token = authorization.removeprefix("Bearer ")

    if settings.DEVPILOT_API_KEY and token == settings.DEVPILOT_API_KEY:
        return await _resolve_n8n_user(session)

    payload = decode_access_token(token)
    if payload is None:
        raise UnauthorizedError("Invalid or expired token")
    return {
        "id": payload["sub"],
        "github_username": payload.get("github_username", ""),
        "pat": payload.get("pat", ""),
    }
