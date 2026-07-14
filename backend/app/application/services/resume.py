from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from structlog import get_logger

from app.core.exceptions import NotFoundError
from app.infrastructure.database.models.job import JobDescriptionModel
from app.infrastructure.database.models.repository import RepositoryModel
from app.infrastructure.database.models.resume import ResumeModel
from app.infrastructure.llm import get_llm_provider

logger = get_logger()


async def create_resume(session: AsyncSession, user_id: Any, raw_text: str, file_path: str | None = None) -> ResumeModel:
    resume = ResumeModel(user_id=user_id, raw_text=raw_text, file_path=file_path)
    session.add(resume)
    await session.commit()
    await session.refresh(resume)
    return resume


async def create_job(session: AsyncSession, user_id: Any, raw_text: str, source_url: str | None = None) -> JobDescriptionModel:
    job = JobDescriptionModel(user_id=user_id, raw_text=raw_text, source_url=source_url)
    session.add(job)
    await session.commit()
    await session.refresh(job)
    return job


async def list_resumes(session: AsyncSession, user_id: Any) -> list[ResumeModel]:
    result = await session.execute(
        select(ResumeModel).where(ResumeModel.user_id == user_id).order_by(ResumeModel.created_at.desc())
    )
    return list(result.scalars().all())


async def list_jobs(session: AsyncSession, user_id: Any) -> list[JobDescriptionModel]:
    result = await session.execute(
        select(JobDescriptionModel).where(JobDescriptionModel.user_id == user_id).order_by(JobDescriptionModel.created_at.desc())
    )
    return list(result.scalars().all())


async def get_resume(session: AsyncSession, resume_id: Any, user_id: Any) -> ResumeModel:
    result = await session.execute(
        select(ResumeModel).where(ResumeModel.id == resume_id, ResumeModel.user_id == user_id)
    )
    resume = result.scalar_one_or_none()
    if resume is None:
        raise NotFoundError(f"Resume {resume_id} not found")
    return resume


async def get_job(session: AsyncSession, job_id: Any, user_id: Any) -> JobDescriptionModel:
    result = await session.execute(
        select(JobDescriptionModel).where(JobDescriptionModel.id == job_id, JobDescriptionModel.user_id == user_id)
    )
    job = result.scalar_one_or_none()
    if job is None:
        raise NotFoundError(f"Job description {job_id} not found")
    return job


async def optimize_resume(
    session: AsyncSession, resume_id: Any, job_id: Any, user_id: Any
) -> dict:
    resume = await get_resume(session, resume_id, user_id)
    job = await get_job(session, job_id, user_id)

    llm = get_llm_provider()
    prompt = f"""Current Resume:
{resume.raw_text}

Target Job Description:
{job.raw_text}

Analyze the resume against the job description and provide:
1. A match score (0-100)
2. Key skills present in the resume that match the job
3. Missing or understated skills/experience
4. Specific suggestions to improve alignment (bullet list)
5. Recommended rewrites for weak sections

Return as structured Markdown."""

    suggestions = await llm.generate(
        prompt,
        system="You are a professional resume reviewer and career coach.",
        max_tokens=2048,
        temperature=0.5,
    )

    return {
        "resume_id": str(resume.id),
        "job_id": str(job.id),
        "suggestions": suggestions,
    }


async def score_match(
    session: AsyncSession, resume_id: Any, job_id: Any, user_id: Any
) -> dict:
    resume = await get_resume(session, resume_id, user_id)
    job = await get_job(session, job_id, user_id)

    llm = get_llm_provider()
    prompt = f"""Resume:
{resume.raw_text}

Job Description:
{job.raw_text}

Rate the match between this resume and job description from 0-100.
Consider: skills match, experience level, keyword alignment, and overall fit.

Return ONLY a JSON object with fields: score (int), strengths (list), gaps (list), summary (str)"""

    result_text = await llm.generate(
        prompt,
        system="You are an ATS (Applicant Tracking System) scoring engine. Return only valid JSON.",
        max_tokens=1024,
        temperature=0.3,
    )

    import json
    try:
        result = json.loads(result_text)
    except json.JSONDecodeError:
        result = {"score": 0, "strengths": [], "gaps": [result_text], "summary": "Could not parse structured response"}

    result["resume_id"] = str(resume.id)
    result["job_id"] = str(job.id)
    return result


async def auto_detect_jobs(session: AsyncSession, user_id: Any) -> list[JobDescriptionModel]:
    result = await session.execute(
        select(RepositoryModel).where(RepositoryModel.user_id == user_id)
    )
    repos = result.scalars().all()
    if not repos:
        return []

    existing = await session.execute(
        select(JobDescriptionModel).where(JobDescriptionModel.user_id == user_id)
    )
    if existing.scalars().first():
        return []

    lang_summary: dict[str, int] = {}
    for r in repos:
        if r.language_stats:
            for lang, _ in r.language_stats.items():
                lang_summary[lang] = lang_summary.get(lang, 0) + 1

    top_langs = sorted(lang_summary, key=lang_summary.get, reverse=True)[:8]
    descs = [r.description for r in repos if r.description]
    desc_sample = descs[:5]

    llm = get_llm_provider()
    prompt = f"""Based on this developer's GitHub profile, generate 3 relevant job descriptions they should target.

Languages used: {", ".join(top_langs)}
Project types: {"; ".join(desc_sample) if desc_sample else "Various software projects"}

For each job description, include the job title at the start and a full paragraph describing responsibilities and required skills.

Return ONLY a JSON array of strings, each being a complete job description starting with the title.
Example: ["Senior Software Engineer - We are looking for...", ...]"""

    result_text = await llm.generate(
        prompt,
        system="You are a career advisor. Generate realistic job descriptions matching the developer's tech stack.",
        max_tokens=2048,
        temperature=0.5,
    )

    import re
    import json
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", result_text.strip(), flags=re.DOTALL)
    try:
        jobs_list = json.loads(cleaned)
    except json.JSONDecodeError:
        jobs_list = [cleaned]

    created = []
    for job_text in jobs_list:
        if isinstance(job_text, str) and len(job_text) > 50:
            j = JobDescriptionModel(user_id=user_id, raw_text=job_text.strip(), source_url="auto-detected")
            session.add(j)
            created.append(j)

    await session.commit()
    for j in created:
        await session.refresh(j)

    logger.info("auto-detected jobs", count=len(created), user_id=str(user_id))
    return created
