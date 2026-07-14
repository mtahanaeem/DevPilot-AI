from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from fastapi.responses import HTMLResponse, PlainTextResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from structlog import get_logger

from app.application.services import portfolio as portfolio_service
from app.infrastructure.database import get_db
from app.presentation.dependencies import get_current_user

logger = get_logger()
router = APIRouter(prefix="/portfolio", tags=["portfolio"])


class PortfolioItemOut(BaseModel):
    id: str
    name: str
    owner: str
    description: str
    language_stats: dict
    stars: int
    forks: int
    last_commit_at: str | None
    is_stale: bool


class PortfolioSummaryOut(BaseModel):
    total_repos: int
    total_stars: int
    total_forks: int
    top_language: str
    languages: dict
    stale_repos: int


class PortfolioOut(BaseModel):
    generated_at: str
    summary: PortfolioSummaryOut
    repositories: list[PortfolioItemOut]


@router.get("")
async def get_portfolio(
    user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> PortfolioOut:
    return await portfolio_service.get_portfolio(session, user["id"])


@router.get("/export", response_class=HTMLResponse)
async def export_portfolio(
    fmt: str = Query("json", pattern="^(json|markdown|html)$"),
    user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    result = await portfolio_service.export_portfolio(session, user["id"], fmt)
    if fmt == "markdown":
        return PlainTextResponse(content=result, media_type="text/markdown")
    elif fmt == "html":
        return HTMLResponse(content=result)
    return result
