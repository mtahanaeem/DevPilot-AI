from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from structlog import get_logger

from app.core.exceptions import NotFoundError
from app.infrastructure.database.models.interview import InterviewSessionModel
from app.infrastructure.database.models.job import JobDescriptionModel
from app.infrastructure.llm import get_llm_provider

logger = get_logger()


async def generate_questions(
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

    llm = get_llm_provider()
    prompt = f"""Based on this job description, generate 10 technical interview questions.

Job Description:
{job.raw_text}

Return a JSON object with:
- questions: array of objects with:
  - id: number (1-10)
  - category: str (e.g., "Algorithms", "System Design", "Language Specific")
  - question: str
  - difficulty: str ("easy", "medium", "hard")

Return ONLY valid JSON."""

    result_text = await llm.generate(
        prompt,
        system="You are a technical interview coach. Generate relevant interview questions for the target role.",
        max_tokens=2048,
        temperature=0.6,
    )

    import re
    import json
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", result_text.strip(), flags=re.DOTALL)
    try:
        questions_data = json.loads(cleaned)
    except json.JSONDecodeError:
        questions_data = {"questions": [{"id": 1, "category": "General", "question": result_text, "difficulty": "medium"}]}

    session_data = InterviewSessionModel(
        user_id=user_id,
        job_description_id=job_id,
        questions={"questions": questions_data.get("questions", [])},
        answers={},
    )
    session.add(session_data)
    await session.commit()
    await session.refresh(session_data)

    return {
        "id": str(session_data.id),
        "job_description_id": str(job_id),
        "questions": questions_data.get("questions", []),
        "created_at": session_data.created_at.isoformat(),
    }


async def submit_answer(
    session: AsyncSession, session_id: Any, user_id: Any, question_id: int, answer: str
) -> dict:
    result = await session.execute(
        select(InterviewSessionModel).where(
            InterviewSessionModel.id == session_id,
            InterviewSessionModel.user_id == user_id,
        )
    )
    interview = result.scalar_one_or_none()
    if interview is None:
        raise NotFoundError(f"Interview session {session_id} not found")

    answers = dict(interview.answers) if isinstance(interview.answers, dict) else {}
    answers[str(question_id)] = answer
    interview.answers = answers
    await session.commit()

    return {"session_id": str(session_id), "question_id": question_id, "status": "saved"}


async def generate_model_answer(
    session: AsyncSession, session_id: Any, user_id: Any, question_id: int
) -> dict:
    result = await session.execute(
        select(InterviewSessionModel).where(
            InterviewSessionModel.id == session_id,
            InterviewSessionModel.user_id == user_id,
        )
    )
    interview = result.scalar_one_or_none()
    if interview is None:
        raise NotFoundError(f"Interview session {session_id} not found")

    questions = interview.questions if isinstance(interview.questions, dict) else {}
    q_list = questions.get("questions", [])
    question_text = ""
    for q in q_list:
        if q.get("id") == question_id:
            question_text = q.get("question", "")
            break

    if not question_text:
        raise NotFoundError(f"Question {question_id} not found in session")

    user_answer = interview.answers.get(str(question_id)) if isinstance(interview.answers, dict) else ""

    llm = get_llm_provider()
    prompt = f"""Question: {question_text}

{'User\'s Answer: ' + user_answer if user_answer else 'No answer provided yet.'}

Generate a model answer for this interview question. Include key points to cover, a structured response, and tips."""

    model_answer = await llm.generate(
        prompt,
        system="You are a senior technical interviewer. Provide model answers with explanations.",
        max_tokens=1024,
        temperature=0.4,
    )

    return {
        "session_id": str(session_id),
        "question_id": question_id,
        "question": question_text,
        "model_answer": model_answer,
    }


async def get_session(session: AsyncSession, session_id: Any, user_id: Any) -> dict:
    result = await session.execute(
        select(InterviewSessionModel).where(
            InterviewSessionModel.id == session_id,
            InterviewSessionModel.user_id == user_id,
        )
    )
    interview = result.scalar_one_or_none()
    if interview is None:
        raise NotFoundError(f"Interview session {session_id} not found")

    questions = interview.questions if isinstance(interview.questions, dict) else {}
    return {
        "id": str(interview.id),
        "job_description_id": str(interview.job_description_id),
        "questions": questions.get("questions", []),
        "created_at": interview.created_at.isoformat(),
    }


async def list_sessions(session: AsyncSession, user_id: Any) -> list[dict]:
    result = await session.execute(
        select(InterviewSessionModel)
        .where(InterviewSessionModel.user_id == user_id)
        .order_by(InterviewSessionModel.created_at.desc())
    )
    sessions = result.scalars().all()
    return [
        {
            "id": str(s.id),
            "job_description_id": str(s.job_description_id),
            "question_count": len(s.questions.get("questions", [])) if isinstance(s.questions, dict) else 0,
            "answer_count": len(s.answers) if isinstance(s.answers, dict) else 0,
            "created_at": s.created_at.isoformat(),
        }
        for s in sessions
    ]
