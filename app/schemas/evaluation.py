"""Evaluation schemas."""

from pydantic import BaseModel, Field
from datetime import datetime


class EvaluationCreateRequest(BaseModel):
    evaluatee_id: int
    score_participation: int = Field(ge=1, le=5)
    score_responsibility: int = Field(ge=1, le=5)
    score_communication: int = Field(ge=1, le=5)
    score_collaboration: int = Field(ge=1, le=5)
    score_creativity: int = Field(ge=1, le=5)
    comment: str | None = None


class EvaluationResponse(BaseModel):
    id: int
    team_id: int
    evaluator_id: int
    evaluatee_id: int
    score_participation: int
    score_responsibility: int
    score_communication: int
    score_collaboration: int
    score_creativity: int
    comment: str | None = None
    created_at: datetime | None = None


class EvalStatusItem(BaseModel):
    """Shows whether the current user has evaluated a specific member."""
    user_id: int
    user_name: str
    evaluated: bool
