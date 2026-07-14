from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from structlog import get_logger

from app.core.exceptions import NotFoundError
from app.infrastructure.database.models.repository import RepositoryModel

logger = get_logger()


async def get_portfolio(session: AsyncSession, user_id: Any) -> dict:
    result = await session.execute(
        select(RepositoryModel)
        .where(RepositoryModel.user_id == user_id)
        .order_by(RepositoryModel.stars.desc())
    )
    repos = result.scalars().all()

    items = []
    for r in repos:
        items.append({
            "id": str(r.id),
            "name": r.name,
            "owner": r.owner,
            "description": r.description or "",
            "language_stats": r.language_stats or {},
            "stars": r.stars,
            "forks": r.forks,
            "last_commit_at": r.last_commit_at.isoformat() if r.last_commit_at else None,
            "is_stale": r.is_stale,
        })

    langs: dict[str, int] = {}
    for r in repos:
        if r.language_stats:
            for lang, pct in r.language_stats.items():
                langs[lang] = langs.get(lang, 0) + 1

    top_lang = max(langs, key=langs.get) if langs else "Unknown"

    return {
        "generated_at": datetime.utcnow().isoformat(),
        "summary": {
            "total_repos": len(repos),
            "total_stars": sum(r.stars for r in repos),
            "total_forks": sum(r.forks for r in repos),
            "top_language": top_lang,
            "languages": langs,
            "stale_repos": sum(1 for r in repos if r.is_stale),
        },
        "repositories": items,
    }


def _to_markdown(portfolio: dict) -> str:
    lines = [
        f"# Portfolio",
        f"",
        f"Generated: {portfolio['generated_at']}",
        f"",
        f"## Summary",
        f"",
        f"- Repositories: {portfolio['summary']['total_repos']}",
        f"- Total Stars: {portfolio['summary']['total_stars']}",
        f"- Total Forks: {portfolio['summary']['total_forks']}",
        f"- Top Language: {portfolio['summary']['top_language']}",
        f"",
        f"## Repositories",
        f"",
    ]
    for repo in portfolio["repositories"]:
        lines.append(f"### [{repo['name']}](https://github.com/{repo['owner']}/{repo['name']})")
        lines.append(f"")
        if repo["description"]:
            lines.append(f"{repo['description']}")
            lines.append(f"")
        lines.append(f"- ★ {repo['stars']} | ⑂ {repo['forks']}")
        lines.append(f"- Language: {', '.join(repo['language_stats'].keys()) or 'N/A'}")
        if repo["is_stale"]:
            lines.append(f"- ⚠️ Stale")
        lines.append(f"")
    return "\n".join(lines)


def _to_html(portfolio: dict) -> str:
    repos_html = ""
    for repo in portfolio["repositories"]:
        stale_tag = '<span style="color:orange">⚠️ Stale</span>' if repo["is_stale"] else ""
        repos_html += f"""
        <div style="border:1px solid #ddd;border-radius:8px;padding:16px;margin-bottom:16px">
            <h3><a href="https://github.com/{repo['owner']}/{repo['name']}" style="text-decoration:none;color:#0366d6">{repo['name']}</a></h3>
            {f'<p>{repo["description"]}</p>' if repo["description"] else ''}
            <p>★ {repo['stars']} | ⑂ {repo['forks']} | {', '.join(repo['language_stats'].keys()) or 'N/A'} {stale_tag}</p>
        </div>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>Portfolio</title></head>
<body style="font-family:system-ui,sans-serif;max-width:800px;margin:auto;padding:20px">
    <h1>Portfolio</h1>
    <p>Generated: {portfolio['generated_at']}</p>
    <h2>Summary</h2>
    <ul>
        <li>Repositories: {portfolio['summary']['total_repos']}</li>
        <li>Total Stars: {portfolio['summary']['total_stars']}</li>
        <li>Total Forks: {portfolio['summary']['total_forks']}</li>
        <li>Top Language: {portfolio['summary']['top_language']}</li>
    </ul>
    <h2>Repositories</h2>
    {repos_html}
</body>
</html>"""


async def export_portfolio(session: AsyncSession, user_id: Any, fmt: str = "json") -> str | dict:
    portfolio = await get_portfolio(session, user_id)

    if fmt == "markdown":
        return _to_markdown(portfolio)
    elif fmt == "html":
        return _to_html(portfolio)
    return portfolio
