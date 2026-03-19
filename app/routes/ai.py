from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.ai import (
    TaskBreakdownRequest,
    TaskBreakdownResponse,
    PrioritySuggestRequest,
    PrioritySuggestResponse,
)
from app.services import ai_service

router = APIRouter()


@router.post(
    "/breakdown",
    response_model=TaskBreakdownResponse,
    summary="AI Task Breakdown",
)
def breakdown_goal(payload: TaskBreakdownRequest):
    """
    **AI Feature**: Provide a high-level goal and Claude will break it into
    concrete, actionable todo tasks with priorities and tags.

    Example goal: *"Launch a personal portfolio website by end of month"*
    """
    return ai_service.breakdown_goal(payload.goal, payload.max_tasks)


@router.post(
    "/suggest-priority",
    response_model=PrioritySuggestResponse,
    summary="AI Priority Suggester",
)
def suggest_priority(payload: PrioritySuggestRequest):
    """
    **AI Feature**: Given a task's title, description, and optional due date,
    Claude suggests the best priority level (low / medium / high) with reasoning.
    """
    return ai_service.suggest_priority(
        payload.title,
        payload.description,
        payload.due_date,
    )
