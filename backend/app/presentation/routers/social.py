from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from structlog import get_logger

from app.application.services import social as social_service
from app.infrastructure.database import get_db
from app.presentation.dependencies import get_current_user

logger = get_logger()
router = APIRouter(prefix="/social", tags=["social"])


class PostOut(BaseModel):
    id: str
    repository_id: str
    platform: str
    content: str
    status: str
    created_at: str


@router.post("/generate")
async def generate_post(
    repo_id: str = Query(...),
    platform: str = Query("linkedin", pattern="^(linkedin|twitter|x)$"),
    tone: str = Query("professional", pattern="^(professional|casual|technical)$"),
    user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> PostOut:
    post = await social_service.generate_post(
        session, user["id"], repo_id, platform, tone, user.get("pat", "")
    )
    return PostOut(
        id=str(post.id),
        repository_id=str(post.repository_id),
        platform=post.platform,
        content=post.content,
        status=post.status,
        created_at=post.created_at.isoformat(),
    )


@router.get("")
async def list_posts(
    user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> list[PostOut]:
    posts = await social_service.list_posts(session, user["id"])
    return [
        PostOut(
            id=str(p.id),
            repository_id=str(p.repository_id),
            platform=p.platform,
            content=p.content,
            status=p.status,
            created_at=p.created_at.isoformat(),
        )
        for p in posts
    ]


@router.post("/{post_id}/approve")
async def approve_post(
    post_id: str,
    user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> PostOut:
    post = await social_service.approve_post(session, post_id, user["id"])
    return PostOut(
        id=str(post.id),
        repository_id=str(post.repository_id),
        platform=post.platform,
        content=post.content,
        status=post.status,
        created_at=post.created_at.isoformat(),
    )
