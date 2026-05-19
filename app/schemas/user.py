"""User profile schemas."""

from pydantic import BaseModel
from datetime import datetime


class UserProfile(BaseModel):
    id: int
    email: str
    name: str
    department: str | None = None
    student_id: str | None = None
    profile_image_url: str | None = None
    residence: str | None = None
    intro: str | None = None
    created_at: datetime | None = None


class UserProfileWithStats(UserProfile):
    """User profile with evaluation statistics."""
    avg_participation: float | None = None
    avg_responsibility: float | None = None
    avg_communication: float | None = None
    avg_collaboration: float | None = None
    avg_creativity: float | None = None
    total_evaluations: int = 0


class UserUpdateRequest(BaseModel):
    name: str | None = None
    department: str | None = None
    student_id: str | None = None
    profile_image_url: str | None = None
    residence: str | None = None
    intro: str | None = None
