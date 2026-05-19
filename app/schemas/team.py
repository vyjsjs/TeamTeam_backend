"""Team management schemas."""

from pydantic import BaseModel
from datetime import date, datetime


class TeamCreateRequest(BaseModel):
    team_name: str
    subject_name: str | None = None
    deadline: date | None = None


class TeamJoinRequest(BaseModel):
    invite_code: str


class TeamResponse(BaseModel):
    id: int
    team_name: str
    subject_name: str | None = None
    invite_code: str
    status: str
    deadline: date | None = None
    leader_id: int
    created_at: datetime | None = None


class TeamListItem(BaseModel):
    id: int
    team_name: str
    subject_name: str | None = None
    status: str
    deadline: date | None = None
    leader_id: int
    member_count: int = 0
    progress: float = 0.0  # percentage of completed tasks


class TeamDashboard(BaseModel):
    """Team main dashboard with summary information."""
    team: TeamResponse
    members: list[dict]
    latest_notice: dict | None = None
    today_tasks: list[dict] = []
    progress: float = 0.0


class TeamStatusUpdate(BaseModel):
    status: str  # '진행중' or '종료'
