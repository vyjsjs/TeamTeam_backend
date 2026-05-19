"""AI Schedule schemas."""

from pydantic import BaseModel
from datetime import date, datetime


class AIScheduleRequest(BaseModel):
    """Request to create an AI schedule session."""
    goal: str  # e.g., "mid 발표"
    deadline: date
    tasks: list[str]  # list of task descriptions, e.g., ["API 명세서 마무리하기", "ERD 완료하기"]


class AIScheduleTaskItem(BaseModel):
    """A single recommended task from AI."""
    id: int | None = None
    task_name: str
    start_date: date | None = None
    due_date: date | None = None


class AIScheduleTaskUpdate(BaseModel):
    """Update a single task's dates."""
    task_name: str | None = None
    start_date: date | None = None
    due_date: date | None = None


class AISessionResponse(BaseModel):
    id: int
    team_id: int
    goal: str
    deadline: date
    status: str
    tasks: list[AIScheduleTaskItem] = []
    created_at: datetime | None = None


class AIConfirmRequest(BaseModel):
    """Request to confirm (and optionally modify) AI-recommended tasks."""
    tasks: list[AIScheduleTaskItem]
