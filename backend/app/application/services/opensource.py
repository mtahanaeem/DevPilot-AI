from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from structlog import get_logger

from app.core.exceptions import NotFoundError
from app.infrastructure.database.models.issue import BookmarkedIssueModel
from app.infrastructure.database.models.repository import RepositoryModel
from app.infrastructure.github import GitHubClient
from app.infrastructure.llm import get_llm_provider

logger = get_logger()


async def search_issues(
    session: AsyncSession, user_id: Any, pat: str, query: str = "", limit: int = 20
) -> list[dict]:
    result = await session.execute(
        select(RepositoryModel).where(RepositoryModel.user_id == user_id)
    )
    repos = result.scalars().all()

    if not repos:
        return []

    repo_qualifiers = " ".join(f"repo:{r.owner}/{r.name}" for r in repos[:5])
    search_query = query or f"good first issues help wanted"

    client = GitHubClient(token=pat)
    try:
        issues_data = await client.search_issues(f"{search_query} {repo_qualifiers}", limit=limit)
    except Exception as exc:
        logger.error("issue search failed", exc_info=exc)
        return []
    finally:
        await client.close()

    # get existing bookmarks to mark them
    existing = await session.execute(
        select(BookmarkedIssueModel.github_issue_id).where(
            BookmarkedIssueModel.user_id == user_id,
            BookmarkedIssueModel.status == "bookmarked",
        )
    )
    bookmarked_ids = {row[0] for row in existing.fetchall()}

    results = []
    for item in issues_data:
        is_bookmarked = item["id"] in bookmarked_ids
        results.append({
            "github_issue_id": item["id"],
            "repo_owner": item["owner"],
            "repo_name": item["repo"],
            "issue_title": item["title"],
            "issue_url": item["html_url"],
            "labels": ", ".join(item.get("labels", [])),
            "score": item.get("score", 0),
            "is_bookmarked": is_bookmarked,
        })

    return results


async def bookmark_issue(
    session: AsyncSession, user_id: Any, issue: dict
) -> dict:
    existing = await session.execute(
        select(BookmarkedIssueModel).where(
            BookmarkedIssueModel.user_id == user_id,
            BookmarkedIssueModel.github_issue_id == issue["github_issue_id"],
        )
    )
    bookmarked = existing.scalar_one_or_none()
    if bookmarked:
        return {"id": str(bookmarked.id), "status": "already_bookmarked"}

    bm = BookmarkedIssueModel(
        user_id=user_id,
        github_issue_id=issue["github_issue_id"],
        repo_owner=issue["repo_owner"],
        repo_name=issue["repo_name"],
        issue_title=issue["issue_title"],
        issue_url=issue["issue_url"],
        labels=issue.get("labels", ""),
        score=issue.get("score"),
        status="bookmarked",
    )
    session.add(bm)
    await session.commit()
    await session.refresh(bm)
    return {"id": str(bm.id), "status": "bookmarked"}


async def dismiss_issue(session: AsyncSession, user_id: Any, issue_id: Any) -> dict:
    result = await session.execute(
        select(BookmarkedIssueModel).where(
            BookmarkedIssueModel.id == issue_id,
            BookmarkedIssueModel.user_id == user_id,
        )
    )
    bm = result.scalar_one_or_none()
    if bm is None:
        raise NotFoundError(f"Issue bookmark {issue_id} not found")
    bm.status = "dismissed"
    await session.commit()
    return {"id": str(issue_id), "status": "dismissed"}


async def list_bookmarked(session: AsyncSession, user_id: Any) -> list[dict]:
    result = await session.execute(
        select(BookmarkedIssueModel)
        .where(
            BookmarkedIssueModel.user_id == user_id,
            BookmarkedIssueModel.status == "bookmarked",
        )
        .order_by(BookmarkedIssueModel.created_at.desc())
    )
    issues = result.scalars().all()
    return [
        {
            "id": str(i.id),
            "github_issue_id": i.github_issue_id,
            "repo_owner": i.repo_owner,
            "repo_name": i.repo_name,
            "issue_title": i.issue_title,
            "issue_url": i.issue_url,
            "labels": i.labels,
            "score": i.score,
            "created_at": i.created_at.isoformat(),
        }
        for i in issues
    ]
