"""Chat schemas."""

from pydantic import BaseModel
from datetime import datetime


class ChatRoomCreateRequest(BaseModel):
    room_name: str | None = None
    member_ids: list[int]  # user IDs to add (creator is auto-included)


class ChatRoomResponse(BaseModel):
    id: int
    team_id: int
    room_name: str | None = None
    created_at: datetime | None = None
    members: list[dict] = []


class ChatMessageResponse(BaseModel):
    id: int
    room_id: int
    sender_id: int
    sender_name: str | None = None
    message_content: str
    created_at: datetime | None = None


class ChatMessageSend(BaseModel):
    message_content: str


class AIPromptResponse(BaseModel):
    prompt: str
