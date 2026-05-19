"""Task schemas."""

from pydantic import BaseModel
from datetime import date, datetime


class TaskCreateRequest(BaseModel):
    task_name: str
    due_date: date | None = None


class TaskUpdateRequest(BaseModel):
    task_name: str | None = None
    due_date: date | None = None
    status: str | None = None  # 'To do', 'In progress', 'Done'


class TaskResponse(BaseModel):
    id: int
    team_id: int
    assignee_id: int | None = None
    assignee_name: str | None = None
    task_name: str
    due_date: date | None = None
    status: str
    created_at: datetime | None = None
    updated_at: datetime | None = None
