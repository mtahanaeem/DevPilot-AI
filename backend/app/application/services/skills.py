from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from structlog import get_logger

from app.core.exceptions import NotFoundError
from app.infrastructure.database.models.job import JobDescriptionModel
from app.infrastructure.database.models.repository import RepositoryModel
from app.infrastructure.database.models.skill import SkillGapReportModel
from app.infrastructure.llm import get_llm_provider

logger = get_logger()


async def infer_skills(session: AsyncSession, user_id: Any) -> list[str]:
    result = await session.execute(
        select(RepositoryModel).where(RepositoryModel.user_id == user_id)
    )
    repos = result.scalars().all()

    skills: set[str] = set()
    for r in repos:
        if r.language_stats:
            skills.update(r.language_stats.keys())
        if r.name:
            parts = r.name.replace("-", " ").replace("_", " ").split()
            skills.update(parts[:3])

    llm = get_llm_provider()
    prompt = f"""From these repositories and detected skills, infer the developer's core technical skills as a comma-separated list.

Repositories:
{chr(10).join(f'- {r.name}: {r.description or "(no desc)"} [{", ".join(r.language_stats.keys())}]' for r in repos[:20])}

Return ONLY a comma-separated list of skills, nothing else."""

    result_text = await llm.generate(
        prompt,
        system="You are a skill assessment expert. Infer developer skills from their GitHub repos.",
        max_tokens=512,
        temperature=0.3,
    )
    import re
    cleaned = re.sub(r"^```(?:text)?\s*|\s*```$", "", result_text.strip(), flags=re.DOTALL)
    llm_skills = [s.strip() for s in cleaned.split(",") if s.strip()]
    return llm_skills


async def analyze_gaps(
    session: AsyncSession, user_id: Any, job_id: Any
) -> dict:
    job_result = await session.execute(
        select(JobDescriptionModel).where(
            JobDescriptionModel.id == job_id,
            JobDescriptionModel.user_id == user_id,
        )
    )
    job = job_result.scalar_one_or_none()
    if job is None:
        raise NotFoundError(f"Job description {job_id} not found")

    current_skills = await infer_skills(session, user_id)
    skills_text = ", ".join(current_skills)

    llm = get_llm_provider()
    prompt = f"""Current Skills: {skills_text}

Job Description:
{job.raw_text}

Analyze the skill gap. Return a JSON object with:
- gaps: list of missing or underdeveloped skills
- present_skills: list of skills that match
- overall_match: percentage (0-100)
- recommendations: list of specific recommendations to close the gaps

Return ONLY valid JSON."""

    result_text = await llm.generate(
        prompt,
        system="You are a skill gap analysis expert. Compare developer skills against job requirements.",
        max_tokens=1024,
        temperature=0.3,
    )

    import re
    import json
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", result_text.strip(), flags=re.DOTALL)
    try:
        result = json.loads(cleaned)
    except json.JSONDecodeError:
        result = {
            "gaps": ["Could not parse analysis"],
            "present_skills": current_skills,
            "overall_match": 0,
            "recommendations": [],
        }

    report = SkillGapReportModel(
        user_id=user_id,
        job_description_id=job_id,
        gaps=result,
    )
    session.add(report)
    await session.commit()
    await session.refresh(report)

    return {
        "id": str(report.id),
        "job_description_id": str(job_id),
        "current_skills": current_skills,
        "gaps": result.get("gaps", []),
        "present_skills": result.get("present_skills", []),
        "overall_match": result.get("overall_match", 0),
        "recommendations": result.get("recommendations", []),
        "created_at": report.created_at.isoformat(),
    }


async def list_reports(session: AsyncSession, user_id: Any) -> list[dict]:
    result = await session.execute(
        select(SkillGapReportModel)
        .where(SkillGapReportModel.user_id == user_id)
        .order_by(SkillGapReportModel.created_at.desc())
    )
    reports = result.scalars().all()
    return [
        {
            "id": str(r.id),
            "job_description_id": str(r.job_description_id),
            "gaps": (r.gaps or {}).get("gaps", []),
            "present_skills": (r.gaps or {}).get("present_skills", []),
            "overall_match": (r.gaps or {}).get("overall_match", 0),
            "recommendations": (r.gaps or {}).get("recommendations", []),
            "created_at": r.created_at.isoformat(),
        }
        for r in reports
    ]
