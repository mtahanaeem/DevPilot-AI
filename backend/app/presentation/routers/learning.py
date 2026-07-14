from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from structlog import get_logger

from app.application.services import learning as learning_service
from app.infrastructure.database import get_db
from app.presentation.dependencies import get_current_user

logger = get_logger()
router = APIRouter(prefix="/learning-plan", tags=["learning"])


class WeekOut(BaseModel):
    week: int
    focus: str
    topics: list[str]
    resources: list[str]
    milestone: str


class PlanOut(BaseModel):
    id: str
    title: str
    goal: str
    weeks: list[WeekOut]
    completed_items: list[dict] | None = None
    created_at: str


class PlanSummaryOut(BaseModel):
    id: str
    title: str
    goal: str
    created_at: str


class UpdateItemOut(BaseModel):
    id: str
    completed_items: list[dict]


@router.post("/generate")
async def generate_plan(
    goals: str = Query("", description="Optional goals/context for the plan"),
    user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> PlanOut:
    return await learning_service.generate_plan(session, user["id"], goals)


@router.get("")
async def list_plans(
    user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> list[PlanSummaryOut]:
    return await learning_service.list_plans(session, user["id"])


@router.get("/{plan_id}")
async def get_plan(
    plan_id: str,
    user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> PlanOut:
    return await learning_service.get_plan(session, plan_id, user["id"])


@router.patch("/{plan_id}/items")
async def update_item_status(
    plan_id: str,
    week_index: int = Query(...),
    topic_index: int = Query(...),
    completed: bool = Query(True),
    user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> UpdateItemOut:
    return await learning_service.update_item_status(
        session, plan_id, user["id"], week_index, topic_index, completed
    )
