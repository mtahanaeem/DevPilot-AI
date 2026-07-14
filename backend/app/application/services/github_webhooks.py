from __future__ import annotations

import hashlib
import hmac
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from structlog import get_logger

from app.core.config import settings
from app.infrastructure.database.models.repository import RepositoryModel
from app.infrastructure.database.models.user import UserModel
from app.infrastructure.github import GitHubClient

logger = get_logger()

WEBHOOK_SECRET = settings.JWT_SECRET or "devpilot-webhook-secret"


def verify_signature(payload_body: bytes, signature_header: str) -> bool:
    if not signature_header:
        return False
    sig_parts = signature_header.split("=")
    if len(sig_parts) != 2:
        return False
    algo, sig = sig_parts
    if algo != "sha256":
        return False
    expected = hmac.new(WEBHOOK_SECRET.encode(), payload_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, sig)


async def handle_push_event(session: AsyncSession, payload: dict[str, Any]) -> None:
    gh_repo = payload.get("repository", {})
    github_repo_id = gh_repo.get("id")
    if not github_repo_id:
        return

    repo = await _find_repo(session, github_repo_id)
    if repo is None:
        logger.warning("push event for untracked repo", github_repo_id=github_repo_id)
        return

    pushed_at_str = gh_repo.get("pushed_at")
    if pushed_at_str:
        repo.last_commit_at = datetime.fromisoformat(pushed_at_str.replace("Z", "+00:00"))
    repo.stars = gh_repo.get("stargazers_count", repo.stars)
    repo.forks = gh_repo.get("forks_count", repo.forks)
    repo.is_stale = False

    await session.commit()
    logger.info("updated repo from push event", repo=repo.name, github_repo_id=github_repo_id)


async def handle_star_event(session: AsyncSession, payload: dict[str, Any]) -> None:
    gh_repo = payload.get("repository", {})
    github_repo_id = gh_repo.get("id")
    if not github_repo_id:
        return

    repo = await _find_repo(session, github_repo_id)
    if repo is None:
        return

    action = payload.get("action", "created")
    repo.stars = gh_repo.get("stargazers_count", repo.stars)
    if action == "created":
        repo.stars = max(0, repo.stars + 1)
    elif action == "deleted":
        repo.stars = max(0, repo.stars - 1)

    await session.commit()
    logger.info("updated repo star count from event", repo=repo.name, stars=repo.stars)


async def handle_release_event(session: AsyncSession, payload: dict[str, Any]) -> None:
    gh_repo = payload.get("repository", {})
    github_repo_id = gh_repo.get("id")
    if not github_repo_id:
        return

    repo = await _find_repo(session, github_repo_id)
    if repo is None:
        return

    logger.info("release event received", repo=repo.name, tag=payload.get("release", {}).get("tag_name"))


async def handle_pull_request_event(session: AsyncSession, payload: dict[str, Any]) -> None:
    gh_repo = payload.get("repository", {})
    github_repo_id = gh_repo.get("id")
    if not github_repo_id:
        return

    repo = await _find_repo(session, github_repo_id)
    if repo is None:
        return

    action = payload.get("action", "")
    pr = payload.get("pull_request", {})
    logger.info("PR event", repo=repo.name, action=action, pr_number=pr.get("number"))


EVENT_HANDLERS: dict[str, Any] = {
    "push": handle_push_event,
    "star": handle_star_event,
    "release": handle_release_event,
    "pull_request": handle_pull_request_event,
}


async def process_webhook(session: AsyncSession, event: str, payload: dict[str, Any]) -> None:
    handler = EVENT_HANDLERS.get(event)
    if handler is None:
        logger.info("unhandled webhook event", event=event)
        return

    try:
        await handler(session, payload)
    except Exception:
        logger.exception("webhook handler failed", event=event)


async def _find_repo(session: AsyncSession, github_repo_id: int) -> RepositoryModel | None:
    result = await session.execute(
        select(RepositoryModel).where(RepositoryModel.github_repo_id == github_repo_id)
    )
    return result.scalar_one_or_none()
