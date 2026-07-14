from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from structlog import get_logger

from app.core.exceptions import NotFoundError
from app.infrastructure.database.models.repository import RepositoryModel
from app.infrastructure.github import GitHubClient

logger = get_logger()


def _lang(gh: dict) -> dict:
    lang = gh.get("language")
    if isinstance(lang, str):
        return {"primary": lang}
    return lang or {}


def _parse_gh_repo(gh: dict, user_id: Any) -> RepositoryModel:
    pushed_at = None
    if gh.get("pushed_at"):
        pushed_at = datetime.fromisoformat(gh["pushed_at"].replace("Z", "+00:00"))
    return RepositoryModel(
        user_id=user_id,
        github_repo_id=gh["id"],
        owner=gh["owner"]["login"],
        name=gh["name"],
        description=gh.get("description") or "",
        language_stats=_lang(gh),
        stars=gh.get("stargazers_count", 0),
        forks=gh.get("forks_count", 0),
        last_commit_at=pushed_at,
        is_stale=False,
    )


def _update_from_gh(repo: RepositoryModel, gh: dict) -> None:
    pushed_at = None
    if gh.get("pushed_at"):
        pushed_at = datetime.fromisoformat(gh["pushed_at"].replace("Z", "+00:00"))
    repo.owner = gh["owner"]["login"]
    repo.name = gh["name"]
    repo.description = gh.get("description") or ""
    repo.language_stats = _lang(gh)
    repo.stars = gh.get("stargazers_count", 0)
    repo.forks = gh.get("forks_count", 0)
    repo.last_commit_at = pushed_at


async def sync_repos(session: AsyncSession, user_id: Any, pat: str) -> list[RepositoryModel]:
    client = GitHubClient(token=pat)
    gh_repos = await client.get_user_repos()
    await client.close()

    synced: list[RepositoryModel] = []
    for gh in gh_repos:
        result = await session.execute(
            select(RepositoryModel).where(RepositoryModel.github_repo_id == gh["id"])
        )
        existing = result.scalar_one_or_none()

        if existing is None:
            repo = _parse_gh_repo(gh, user_id)
            session.add(repo)
            synced.append(repo)
        else:
            _update_from_gh(existing, gh)
            synced.append(existing)

    await session.commit()
    for r in synced:
        await session.refresh(r)

    logger.info("synced repos", count=len(synced), user_id=str(user_id))
    return synced


async def sync_single_repo(session: AsyncSession, user_id: Any, pat: str, owner: str, repo_name: str) -> RepositoryModel:
    client = GitHubClient(token=pat)
    gh = await client.get_repo(owner, repo_name)
    await client.close()

    result = await session.execute(
        select(RepositoryModel).where(RepositoryModel.github_repo_id == gh["id"])
    )
    existing = result.scalar_one_or_none()

    if existing is None:
        repo = _parse_gh_repo(gh, user_id)
        session.add(repo)
    else:
        _update_from_gh(existing, gh)
        repo = existing

    await session.commit()
    await session.refresh(repo)
    return repo


async def list_repos(session: AsyncSession, user_id: Any) -> list[RepositoryModel]:
    result = await session.execute(
        select(RepositoryModel).where(RepositoryModel.user_id == user_id).order_by(RepositoryModel.stars.desc())
    )
    return list(result.scalars().all())


async def get_repo(session: AsyncSession, user_id: Any, repo_id: Any) -> RepositoryModel:
    result = await session.execute(
        select(RepositoryModel).where(RepositoryModel.id == repo_id, RepositoryModel.user_id == user_id)
    )
    repo = result.scalar_one_or_none()
    if repo is None:
        raise NotFoundError(f"RepositoryModel {repo_id} not found")
    return repo


async def get_repo_by_gh_id(session: AsyncSession, github_repo_id: int) -> RepositoryModel | None:
    result = await session.execute(
        select(RepositoryModel).where(RepositoryModel.github_repo_id == github_repo_id)
    )
    return result.scalar_one_or_none()


async def flag_stale_repos(session: AsyncSession, user_id: Any, days: int = 90) -> list[RepositoryModel]:
    threshold = datetime.now(timezone.utc)
    result = await session.execute(
        select(RepositoryModel).where(RepositoryModel.user_id == user_id)
    )
    repos = list(result.scalars().all())
    stale: list[RepositoryModel] = []
    for repo in repos:
        if repo.last_commit_at is None:
            continue
        days_stale = (threshold - repo.last_commit_at).days
        if days_stale > days and not repo.is_stale:
            repo.is_stale = True
            stale.append(repo)
        elif days_stale <= days and repo.is_stale:
            repo.is_stale = False

    await session.commit()
    for r in stale:
        await session.refresh(r)

    return stale
