from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from structlog import get_logger

from app.application.services import skills as skills_service
from app.infrastructure.database import get_db
from app.presentation.dependencies import get_current_user

logger = get_logger()
router = APIRouter(prefix="/skills", tags=["skills"])


class SkillsOut(BaseModel):
    skills: list[str]


class GapAnalysisOut(BaseModel):
    id: str
    job_description_id: str
    current_skills: list[str]
    gaps: list[str]
    present_skills: list[str]
    overall_match: int
    recommendations: list[str]
    created_at: str


class GapReport(BaseModel):
    id: str
    job_description_id: str
    gaps: list[str]
    present_skills: list[str]
    overall_match: int
    recommendations: list[str]
    created_at: str


@router.get("/infer")
async def infer_skills(
    user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> SkillsOut:
    skills = await skills_service.infer_skills(session, user["id"])
    return SkillsOut(skills=skills)


@router.post("/analyze/{job_id}")
async def analyze_gaps(
    job_id: str,
    user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> GapAnalysisOut:
    return await skills_service.analyze_gaps(session, user["id"], job_id)


@router.get("/reports")
async def list_reports(
    user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> list[GapReport]:
    return await skills_service.list_reports(session, user["id"])
