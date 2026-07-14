from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from structlog import get_logger

from app.core.exceptions import NotFoundError
from app.infrastructure.database.models.learning import LearningPlanModel
from app.infrastructure.llm import get_llm_provider

logger = get_logger()


async def generate_plan(session: AsyncSession, user_id: Any, goals: str = "") -> dict:
    llm = get_llm_provider()
    prompt = f"""Generate a structured 4-week learning plan to help a developer upskill.

Additional goals/context: {goals or "General full-stack development improvement"}

Return a JSON object with:
- title: str
- goal: str
- weeks: array of objects with:
  - week: int (1-4)
  - focus: str
  - topics: array of strings
  - resources: array of strings (specific courses, docs, repos)
  - milestone: str

Return ONLY valid JSON."""

    result_text = await llm.generate(
        prompt,
        system="You are a learning and development planner. Create structured weekly learning plans.",
        max_tokens=2048,
        temperature=0.5,
    )

    import json
    try:
        plan_data = json.loads(result_text)
    except json.JSONDecodeError:
        plan_data = {
            "title": "Learning Plan",
            "goal": goals or "Upskill",
            "weeks": [
                {"week": 1, "focus": "Foundation", "topics": [], "resources": [], "milestone": ""}
            ],
        }

    plan = LearningPlanModel(
        user_id=user_id,
        items=plan_data,
    )
    session.add(plan)
    await session.commit()
    await session.refresh(plan)

    return {
        "id": str(plan.id),
        "title": plan_data.get("title", "Learning Plan"),
        "goal": plan_data.get("goal", ""),
        "weeks": plan_data.get("weeks", []),
        "created_at": plan.created_at.isoformat(),
    }


async def get_plan(session: AsyncSession, plan_id: Any, user_id: Any) -> dict:
    result = await session.execute(
        select(LearningPlanModel).where(
            LearningPlanModel.id == plan_id,
            LearningPlanModel.user_id == user_id,
        )
    )
    plan = result.scalar_one_or_none()
    if plan is None:
        raise NotFoundError(f"Learning plan {plan_id} not found")
    items = plan.items if isinstance(plan.items, dict) else {}
    return {
        "id": str(plan.id),
        "title": items.get("title", "Learning Plan"),
        "goal": items.get("goal", ""),
        "weeks": items.get("weeks", []),
        "completed_items": items.get("completed_items", []),
        "created_at": plan.created_at.isoformat(),
    }


async def list_plans(session: AsyncSession, user_id: Any) -> list[dict]:
    result = await session.execute(
        select(LearningPlanModel)
        .where(LearningPlanModel.user_id == user_id)
        .order_by(LearningPlanModel.created_at.desc())
    )
    plans = result.scalars().all()
    return [
        {
            "id": str(p.id),
            "title": p.items.get("title", "Learning Plan") if isinstance(p.items, dict) else "Learning Plan",
            "goal": p.items.get("goal", "") if isinstance(p.items, dict) else "",
            "created_at": p.created_at.isoformat(),
        }
        for p in plans
    ]


async def update_item_status(
    session: AsyncSession, plan_id: Any, user_id: Any, week_index: int, topic_index: int, completed: bool
) -> dict:
    result = await session.execute(
        select(LearningPlanModel).where(
            LearningPlanModel.id == plan_id,
            LearningPlanModel.user_id == user_id,
        )
    )
    plan = result.scalar_one_or_none()
    if plan is None:
        raise NotFoundError(f"Learning plan {plan_id} not found")

    items = dict(plan.items) if isinstance(plan.items, dict) else {}
    completed_items = list(items.get("completed_items", []))
    entry = {"week": week_index, "topic": topic_index}

    if completed and entry not in completed_items:
        completed_items.append(entry)
    elif not completed and entry in completed_items:
        completed_items.remove(entry)

    items["completed_items"] = completed_items
    plan.items = items
    await session.commit()

    return {"id": str(plan.id), "completed_items": completed_items}
