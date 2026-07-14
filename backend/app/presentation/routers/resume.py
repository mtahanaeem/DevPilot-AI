from __future__ import annotations

from fastapi import APIRouter, Depends, Form, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from structlog import get_logger

from app.application.services import resume as resume_service
from app.infrastructure.database import get_db
from app.presentation.dependencies import get_current_user

logger = get_logger()
router = APIRouter(prefix="/resume", tags=["resume"])


class ResumeOut(BaseModel):
    id: str
    raw_text: str
    file_path: str | None
    created_at: str


class JobOut(BaseModel):
    id: str
    raw_text: str
    source_url: str | None
    created_at: str


class SuggestionOut(BaseModel):
    resume_id: str
    job_id: str
    suggestions: str


class ScoreOut(BaseModel):
    resume_id: str
    job_id: str
    score: int
    strengths: list[str]
    gaps: list[str]
    summary: str


@router.post("/upload")
async def upload_resume(
    text: str = Form(...),
    user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> ResumeOut:
    resume = await resume_service.create_resume(session, user["id"], text)
    return ResumeOut(
        id=str(resume.id),
        raw_text=resume.raw_text,
        file_path=resume.file_path,
        created_at=resume.created_at.isoformat(),
    )


@router.post("/text")
async def add_resume_text(
    text: str = Form(...),
    user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> ResumeOut:
    resume = await resume_service.create_resume(session, user["id"], text)
    return ResumeOut(
        id=str(resume.id),
        raw_text=resume.raw_text,
        file_path=resume.file_path,
        created_at=resume.created_at.isoformat(),
    )


@router.get("")
async def list_resumes(
    user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> list[ResumeOut]:
    resumes = await resume_service.list_resumes(session, user["id"])
    return [
        ResumeOut(id=str(r.id), raw_text=r.raw_text, file_path=r.file_path, created_at=r.created_at.isoformat())
        for r in resumes
    ]


@router.post("/jobs")
async def add_job(
    text: str = Form(...),
    source_url: str = Query(""),
    user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> JobOut:
    job = await resume_service.create_job(session, user["id"], text, source_url or None)
    return JobOut(
        id=str(job.id),
        raw_text=job.raw_text,
        source_url=job.source_url,
        created_at=job.created_at.isoformat(),
    )


@router.get("/jobs")
async def list_jobs(
    user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> list[JobOut]:
    jobs = await resume_service.list_jobs(session, user["id"])
    return [
        JobOut(id=str(j.id), raw_text=j.raw_text, source_url=j.source_url, created_at=j.created_at.isoformat())
        for j in jobs
    ]


@router.post("/jobs/auto-detect")
async def auto_detect_jobs(
    user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> list[JobOut]:
    jobs = await resume_service.auto_detect_jobs(session, user["id"])
    return [
        JobOut(id=str(j.id), raw_text=j.raw_text, source_url=j.source_url, created_at=j.created_at.isoformat())
        for j in jobs
    ]


@router.post("/{resume_id}/optimize")
async def optimize_resume(
    resume_id: str,
    job_id: str = Query(...),
    user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> SuggestionOut:
    result = await resume_service.optimize_resume(session, resume_id, job_id, user["id"])
    return SuggestionOut(**result)


@router.post("/{resume_id}/score")
async def score_resume(
    resume_id: str,
    job_id: str = Query(...),
    user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> ScoreOut:
    result = await resume_service.score_match(session, resume_id, job_id, user["id"])
    return ScoreOut(**result)
