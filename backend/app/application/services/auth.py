from __future__ import annotations

from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from structlog import get_logger

from app.core.config import settings
from app.core.security import create_access_token
from app.infrastructure.database.models.user import UserModel

logger = get_logger()

GITHUB_API = "https://api.github.com"


async def authenticate_with_pat(session: AsyncSession, pat: str) -> dict[str, Any]:
    async with httpx.AsyncClient(
        base_url=GITHUB_API,
        headers={"Authorization": f"Bearer {pat}", "Accept": "application/vnd.github.v3+json", "User-Agent": "DevPilot-AI/1.0"},
        timeout=15.0,
    ) as client:
        resp = await client.get("/user")
        resp.raise_for_status()
        gh_user = resp.json()

    github_username: str = gh_user["login"]

    result = await session.execute(select(UserModel).where(UserModel.github_username == github_username))
    user = result.scalar_one_or_none()

    if user is None:
        user = UserModel(github_username=github_username, oauth_token=pat)
        session.add(user)
        await session.commit()
        await session.refresh(user)
        logger.info("created user", github_username=github_username)
    else:
        user.oauth_token = pat
        await session.commit()
        await session.refresh(user)
        logger.info("updated user token", github_username=github_username)

    token = create_access_token({"sub": str(user.id), "github_username": github_username, "pat": pat})
    return {"access_token": token, "token_type": "bearer", "user": {"id": str(user.id), "github_username": github_username}}


def get_oauth_url() -> str:
    return (
        f"https://github.com/login/oauth/authorize"
        f"?client_id={settings.GITHUB_CLIENT_ID}"
        f"&redirect_uri={settings.BACKEND_URL}/auth/callback"
        f"&scope=repo,read:user"
    )


async def handle_oauth_callback(session: AsyncSession, code: str) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=15.0) as client:
        token_resp = await client.post(
            "https://github.com/login/oauth/access_token",
            json={
                "client_id": settings.GITHUB_CLIENT_ID,
                "client_secret": settings.GITHUB_CLIENT_SECRET,
                "code": code,
            },
            headers={"Accept": "application/json"},
        )
        token_resp.raise_for_status()
        token_data = token_resp.json()
        pat = token_data.get("access_token", "")

    if not pat:
        raise ValueError("Failed to exchange OAuth code for token")

    return await authenticate_with_pat(session, pat)
