"""Reference room schemas."""

from pydantic import BaseModel
from datetime import datetime


class ReferenceCreateRequest(BaseModel):
    file_name: str
    file_url: str


class ReferenceResponse(BaseModel):
    id: int
    team_id: int
    uploader_id: int
    uploader_name: str | None = None
    file_name: str
    file_url: str
    created_at: datetime | None = None
