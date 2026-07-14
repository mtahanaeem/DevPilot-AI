from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from structlog import get_logger

from app.application.services import repository as repo_service
from app.application.services.resume import auto_detect_jobs
from app.core.config import settings
from app.infrastructure.database import get_db
from app.infrastructure.github import GitHubClient
from app.presentation.dependencies import get_current_user

logger = get_logger()
router = APIRouter(prefix="/repositories", tags=["repositories"])


class RepoOut(BaseModel):
    id: str
    github_repo_id: int
    owner: str
    name: str
    description: str | None
    language_stats: dict
    stars: int
    forks: int
    last_commit_at: str | None
    is_stale: bool


class WebhookOut(BaseModel):
    id: int
    url: str
    active: bool
    events: list[str]


@router.get("")
async def list_repos(
    user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> list[RepoOut]:
    repos = await repo_service.list_repos(session, user["id"])
    return [
        RepoOut(
            id=str(r.id),
            github_repo_id=r.github_repo_id,
            owner=r.owner,
            name=r.name,
            description=r.description,
            language_stats=r.language_stats or {},
            stars=r.stars,
            forks=r.forks,
            last_commit_at=r.last_commit_at.isoformat() if r.last_commit_at else None,
            is_stale=r.is_stale,
        )
        for r in repos
    ]


@router.post("/sync")
async def sync_repos(
    user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> dict:
    repos = await repo_service.sync_repos(session, user["id"], user.get("pat", ""))
    await auto_detect_jobs(session, user["id"])
    return {
        "repos": [
            RepoOut(
                id=str(r.id),
                github_repo_id=r.github_repo_id,
                owner=r.owner,
                name=r.name,
                description=r.description,
                language_stats=r.language_stats or {},
                stars=r.stars,
                forks=r.forks,
                last_commit_at=r.last_commit_at.isoformat() if r.last_commit_at else None,
                is_stale=r.is_stale,
            )
            for r in repos
        ]
    }


@router.get("/stale")
async def get_stale_repos(
    days: int = Query(90, ge=1),
    user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> dict:
    repos = await repo_service.flag_stale_repos(session, user["id"], days=days)
    return {
        "repos": [
            RepoOut(
                id=str(r.id),
                github_repo_id=r.github_repo_id,
                owner=r.owner,
                name=r.name,
                description=r.description,
                language_stats=r.language_stats or {},
                stars=r.stars,
                forks=r.forks,
                last_commit_at=r.last_commit_at.isoformat() if r.last_commit_at else None,
                is_stale=r.is_stale,
            )
            for r in repos
        ]
    }


@router.get("/{repo_id}")
async def get_repo(
    repo_id: str,
    user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> RepoOut:
    repo = await repo_service.get_repo(session, user["id"], repo_id)
    return RepoOut(
        id=str(repo.id),
        github_repo_id=repo.github_repo_id,
        owner=repo.owner,
        name=repo.name,
        description=repo.description,
        language_stats=repo.language_stats or {},
        stars=repo.stars,
        forks=repo.forks,
        last_commit_at=repo.last_commit_at.isoformat() if repo.last_commit_at else None,
        is_stale=repo.is_stale,
    )


@router.get("/{repo_id}/webhooks")
async def list_webhooks(
    repo_id: str,
    user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> list[WebhookOut]:
    repo = await repo_service.get_repo(session, user["id"], repo_id)
    client = GitHubClient(token=user.get("pat", ""))
    try:
        hooks = await client.list_webhooks(repo.owner, repo.name)
        return [
            WebhookOut(id=h["id"], url=h["config"]["url"], active=h["active"], events=h["events"])
            for h in hooks
        ]
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))
    finally:
        await client.close()


@router.post("/{repo_id}/webhooks")
async def create_webhook(
    repo_id: str,
    user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> WebhookOut:
    repo = await repo_service.get_repo(session, user["id"], repo_id)
    callback_url = f"{settings.BACKEND_URL}/github/webhook"
    client = GitHubClient(token=user.get("pat", ""))
    try:
        hook = await client.create_webhook(repo.owner, repo.name, callback_url, settings.JWT_SECRET)
        return WebhookOut(id=hook["id"], url=hook["config"]["url"], active=hook["active"], events=hook["events"])
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))
    finally:
        await client.close()
