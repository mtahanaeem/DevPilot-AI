from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from structlog import get_logger

from app.application.services import interview as interview_service
from app.infrastructure.database import get_db
from app.presentation.dependencies import get_current_user

logger = get_logger()
router = APIRouter(prefix="/interview", tags=["interview"])


class QuestionOut(BaseModel):
    id: int
    category: str
    question: str
    difficulty: str


class SessionOut(BaseModel):
    id: str
    job_description_id: str
    questions: list[QuestionOut]
    created_at: str


class AnswerOut(BaseModel):
    session_id: str
    question_id: int
    status: str


class ModelAnswerOut(BaseModel):
    session_id: str
    question_id: int
    question: str
    model_answer: str


class SessionSummaryOut(BaseModel):
    id: str
    job_description_id: str
    question_count: int
    answer_count: int
    created_at: str


@router.post("/generate/{job_id}")
async def generate_questions(
    job_id: str,
    user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> SessionOut:
    return await interview_service.generate_questions(session, user["id"], job_id)


@router.post("/{session_id}/answer")
async def submit_answer(
    session_id: str,
    question_id: int = Query(...),
    answer: str = Query(...),
    user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> AnswerOut:
    return await interview_service.submit_answer(session, session_id, user["id"], question_id, answer)


@router.get("/{session_id}/model-answer")
async def get_model_answer(
    session_id: str,
    question_id: int = Query(...),
    user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> ModelAnswerOut:
    return await interview_service.generate_model_answer(session, session_id, user["id"], question_id)


@router.get("")
async def list_sessions(
    user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> list[SessionSummaryOut]:
    return await interview_service.list_sessions(session, user["id"])


@router.get("/{session_id}")
async def get_session(
    session_id: str,
    user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> SessionOut:
    return await interview_service.get_session(session, session_id, user["id"])
