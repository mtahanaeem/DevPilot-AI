from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from structlog import get_logger

from app.application.services import opensource as oss_service
from app.infrastructure.database import get_db
from app.presentation.dependencies import get_current_user

logger = get_logger()
router = APIRouter(prefix="/opensource", tags=["opensource"])


class IssueOut(BaseModel):
    github_issue_id: int
    repo_owner: str
    repo_name: str
    issue_title: str
    issue_url: str
    labels: str
    score: float | None
    is_bookmarked: bool


class BookmarkOut(BaseModel):
    id: str
    status: str


class BookmarkedIssueOut(BaseModel):
    id: str
    github_issue_id: int
    repo_owner: str
    repo_name: str
    issue_title: str
    issue_url: str
    labels: str
    score: float | None
    created_at: str


class BookmarkRequest(BaseModel):
    github_issue_id: int
    repo_owner: str
    repo_name: str
    issue_title: str
    issue_url: str
    labels: str = ""
    score: float | None = None


@router.get("/search")
async def search_issues(
    query: str = Query("", description="Optional search query"),
    limit: int = Query(20, ge=1, le=100),
    user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> list[IssueOut]:
    return await oss_service.search_issues(session, user["id"], user.get("pat", ""), query, limit)


@router.post("/bookmark")
async def bookmark_issue(
    issue: BookmarkRequest,
    user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> BookmarkOut:
    return await oss_service.bookmark_issue(session, user["id"], issue.model_dump())


@router.post("/{issue_id}/dismiss")
async def dismiss_issue(
    issue_id: str,
    user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> BookmarkOut:
    return await oss_service.dismiss_issue(session, user["id"], issue_id)


@router.get("/bookmarked")
async def list_bookmarked(
    user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> list[BookmarkedIssueOut]:
    return await oss_service.list_bookmarked(session, user["id"])
