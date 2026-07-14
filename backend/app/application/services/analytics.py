from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from structlog import get_logger

from app.infrastructure.database.models.analytics import AnalyticsSnapshotModel
from app.infrastructure.database.models.repository import RepositoryModel
from app.infrastructure.llm import get_llm_provider

logger = get_logger()


async def get_dashboard(session: AsyncSession, user_id: Any) -> dict:
    result = await session.execute(
        select(RepositoryModel).where(RepositoryModel.user_id == user_id)
    )
    repos = result.scalars().all()

    total_repos = len(repos)
    total_stars = sum(r.stars for r in repos)
    total_forks = sum(r.forks for r in repos)
    stale_count = sum(1 for r in repos if r.is_stale)

    lang_dist: dict[str, int] = {}
    for r in repos:
        if r.language_stats:
            for lang in r.language_stats:
                lang_dist[lang] = lang_dist.get(lang, 0) + 1

    top_langs = sorted(lang_dist.items(), key=lambda x: x[1], reverse=True)[:10]

    now = datetime.now(timezone.utc)
    recent = [r for r in repos if r.last_commit_at and (now - r.last_commit_at).days <= 30]
    active_count = len(recent)

    return {
        "total_repos": total_repos,
        "total_stars": total_stars,
        "total_forks": total_forks,
        "stale_count": stale_count,
        "active_count": active_count,
        "language_distribution": [{"language": k, "count": v} for k, v in top_langs],
        "repos": [
            {
                "name": r.name,
                "owner": r.owner,
                "stars": r.stars,
                "forks": r.forks,
                "language": list(r.language_stats.keys())[0] if r.language_stats else "Unknown",
                "last_commit_at": r.last_commit_at.isoformat() if r.last_commit_at else None,
                "is_stale": r.is_stale,
            }
            for r in repos
        ],
    }


async def generate_weekly_report(session: AsyncSession, user_id: Any) -> dict:
    result = await session.execute(
        select(RepositoryModel).where(RepositoryModel.user_id == user_id)
    )
    repos = result.scalars().all()

    total_stars = sum(r.stars for r in repos)
    total_forks = sum(r.forks for r in repos)
    stale = [r for r in repos if r.is_stale]

    now = datetime.now(timezone.utc)
    active_30 = sum(1 for r in repos if r.last_commit_at and (now - r.last_commit_at).days <= 30)

    langs: set[str] = set()
    for r in repos:
        if r.language_stats:
            langs.update(r.language_stats.keys())

    llm = get_llm_provider()
    prompt = f"""Generate a weekly career report summary for a developer with {len(repos)} tracked repositories.

Stats:
- Total Stars: {total_stars}
- Total Forks: {total_forks}
- Active repos (committed in last 30 days): {active_30}
- Stale repos needing attention: {len(stale)}
- Languages: {", ".join(sorted(langs)) if langs else "N/A"}

Return a JSON object with:
- summary: str (2-3 sentence overview)
- highlights: list[str] (achievements this week)
- recommendations: list[str] (action items for next week)

Return ONLY valid JSON."""

    result_text = await llm.generate(
        prompt,
        system="You are a career analytics assistant. Summarize weekly GitHub activity.",
        max_tokens=1024,
        temperature=0.5,
    )

    import re
    import json
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", result_text.strip(), flags=re.DOTALL)
    try:
        report_data = json.loads(cleaned)
    except json.JSONDecodeError:
        report_data = {"summary": "Weekly report generated.", "highlights": [], "recommendations": []}

    snapshot = AnalyticsSnapshotModel(
        user_id=user_id,
        period="weekly",
        metrics={
            "total_repos": len(repos),
            "total_stars": total_stars,
            "total_forks": total_forks,
            "stale_count": len(stale),
            "report": report_data,
        },
    )
    session.add(snapshot)
    await session.commit()
    await session.refresh(snapshot)

    return {
        "id": str(snapshot.id),
        "period": "weekly",
        "summary": report_data.get("summary", ""),
        "highlights": report_data.get("highlights", []),
        "recommendations": report_data.get("recommendations", []),
        "metrics": {
            "total_repos": len(repos),
            "total_stars": total_stars,
            "total_forks": total_forks,
            "stale_count": len(stale),
        },
        "created_at": snapshot.created_at.isoformat(),
    }


async def list_reports(session: AsyncSession, user_id: Any) -> list[dict]:
    result = await session.execute(
        select(AnalyticsSnapshotModel)
        .where(AnalyticsSnapshotModel.user_id == user_id)
        .order_by(AnalyticsSnapshotModel.created_at.desc())
        .limit(10)
    )
    snapshots = result.scalars().all()
    return [
        {
            "id": str(s.id),
            "period": s.period,
            "metrics": s.metrics if isinstance(s.metrics, dict) else {},
            "created_at": s.created_at.isoformat(),
        }
        for s in snapshots
    ]
