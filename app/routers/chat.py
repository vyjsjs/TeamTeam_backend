"""Chat routes: rooms, messages, AI prompt generation."""

import json
import logging
import time
from fastapi import APIRouter, Depends, HTTPException, Request
from app.dependencies import get_current_user
from app.core.supabase import get_supabase
from app.core.config import get_settings
from app.schemas.chat import ChatRoomCreateRequest, ChatRoomResponse, ChatMessageResponse, ChatMessageSend, AIPromptResponse
from app.core.metrics import (
    ai_chat_summary_latency,
    ai_chat_external_latency,
    ai_chat_disconnect_total,
)

router = APIRouter(tags=["Chat"])
logger = logging.getLogger("teamteam")

AI_CHAT_WARN_THRESHOLD_S = 5.0


def _verify_member(db, team_id: int, user_id: int):
    r = db.table("team_member").select("id").eq("team_id", team_id).eq("user_id", user_id).execute()
    if not r.data:
        raise HTTPException(status_code=403, detail="해당 팀의 멤버가 아닙니다.")


@router.post("/api/teams/{team_id}/chat-rooms", response_model=ChatRoomResponse, status_code=201)
async def create_chat_room(team_id: int, body: ChatRoomCreateRequest, current_user: dict = Depends(get_current_user)):
    """채팅방 생성 — 참여자 선택."""
    db = get_supabase()
    _verify_member(db, team_id, current_user["id"])

    room = db.table("chat_room").insert({"team_id": team_id, "room_name": body.room_name}).execute()
    if not room.data:
        raise HTTPException(status_code=500, detail="채팅방 생성에 실패했습니다.")

    room_id = room.data[0]["id"]
    member_ids = set(body.member_ids)
    member_ids.add(current_user["id"])

    for uid in member_ids:
        db.table("chat_room_member").insert({"room_id": room_id, "user_id": uid}).execute()

    return ChatRoomResponse(id=room_id, team_id=team_id, room_name=body.room_name, created_at=room.data[0].get("created_at"))


@router.get("/api/teams/{team_id}/chat-rooms", response_model=list[ChatRoomResponse])
async def list_chat_rooms(team_id: int, current_user: dict = Depends(get_current_user)):
    """내가 속한 채팅방 목록."""
    db = get_supabase()
    _verify_member(db, team_id, current_user["id"])

    my_rooms = db.table("chat_room_member").select("room_id").eq("user_id", current_user["id"]).execute()
    if not my_rooms.data:
        return []

    room_ids = [r["room_id"] for r in my_rooms.data]
    rooms = db.table("chat_room").select("*").in_("id", room_ids).eq("team_id", team_id).order("created_at", desc=True).execute()

    return [ChatRoomResponse(id=r["id"], team_id=r["team_id"], room_name=r.get("room_name"), created_at=r.get("created_at")) for r in rooms.data or []]


@router.get("/api/chat-rooms/{room_id}/messages", response_model=list[ChatMessageResponse])
async def list_messages(room_id: int, current_user: dict = Depends(get_current_user)):
    """메시지 내역 조회."""
    db = get_supabase()

    membership = db.table("chat_room_member").select("room_id").eq("room_id", room_id).eq("user_id", current_user["id"]).execute()
    if not membership.data:
        raise HTTPException(status_code=403, detail="채팅방 멤버가 아닙니다.")

    msgs = db.table("chat_message").select("*, sender:sender_id(name)").eq("room_id", room_id).order("created_at").execute()

    result = []
    for m in msgs.data or []:
        sname = m.get("sender", {}).get("name") if m.get("sender") else None
        result.append(ChatMessageResponse(id=m["id"], room_id=m["room_id"], sender_id=m["sender_id"], sender_name=sname, message_content=m["message_content"], created_at=m.get("created_at")))
    return result


@router.post("/api/chat-rooms/{room_id}/messages", response_model=ChatMessageResponse, status_code=201)
async def send_message(room_id: int, body: ChatMessageSend, current_user: dict = Depends(get_current_user)):
    """메시지 전송."""
    db = get_supabase()
    membership = db.table("chat_room_member").select("room_id").eq("room_id", room_id).eq("user_id", current_user["id"]).execute()
    if not membership.data:
        raise HTTPException(status_code=403, detail="채팅방 멤버가 아닙니다.")

    msg = db.table("chat_message").insert({"room_id": room_id, "sender_id": current_user["id"], "message_content": body.message_content}).execute()
    if not msg.data:
        raise HTTPException(status_code=500, detail="메시지 전송에 실패했습니다.")

    m = msg.data[0]
    return ChatMessageResponse(id=m["id"], room_id=m["room_id"], sender_id=m["sender_id"], sender_name=current_user["name"], message_content=m["message_content"], created_at=m.get("created_at"))


@router.post("/api/chat-rooms/{room_id}/ai-prompt", response_model=AIPromptResponse)
async def generate_ai_prompt(room_id: int, request: Request, current_user: dict = Depends(get_current_user)):
    """대화 내용 기반 AI 프롬프트/요약 생성."""
    endpoint_start = time.time()

    db = get_supabase()
    membership = db.table("chat_room_member").select("room_id").eq("room_id", room_id).eq("user_id", current_user["id"]).execute()
    if not membership.data:
        raise HTTPException(status_code=403, detail="채팅방 멤버가 아닙니다.")

    msgs = db.table("chat_message").select("message_content, sender:sender_id(name)").eq("room_id", room_id).order("created_at", desc=True).limit(50).execute()

    if not msgs.data:
        raise HTTPException(status_code=400, detail="대화 내역이 없습니다.")

    conversation = "\n".join(
        f"{m.get('sender', {}).get('name', '?')}: {m['message_content']}"
        for m in reversed(msgs.data)
    )

    settings = get_settings()
    if not settings.GEMINI_API_KEY:
        total = time.time() - endpoint_start
        ai_chat_summary_latency.observe(total)
        return AIPromptResponse(prompt=f"[최근 대화 요약]\n{conversation[:500]}...")

    import google.generativeai as genai
    genai.configure(api_key=settings.GEMINI_API_KEY)

    # Client disconnect check before expensive external call
    if await request.is_disconnected():
        ai_chat_disconnect_total.inc()
        logger.warning(
            "AI chat summary: client disconnected before external API call",
            extra={"extra_data": {"room_id": room_id, "user_id": current_user["id"]}},
        )
        raise HTTPException(status_code=499, detail="클라이언트 연결이 끊겼습니다.")

    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        prompt_text = f"다음 팀 프로젝트 채팅 대화를 분석하여 주요 논의 사항, 결정된 내용, 남은 과제를 정리해주세요. 한국어로 답변하세요.\n\n대화내용:\n{conversation}"

        ext_start = time.time()
        response = model.generate_content(prompt_text)
        ext_latency = time.time() - ext_start
        ai_chat_external_latency.observe(ext_latency)

        total_latency = time.time() - endpoint_start
        ai_chat_summary_latency.observe(total_latency)

        log_extra = {
            "room_id": room_id,
            "user_id": current_user["id"],
            "total_latency_ms": round(total_latency * 1000, 2),
            "external_api_latency_ms": round(ext_latency * 1000, 2),
        }
        if total_latency > AI_CHAT_WARN_THRESHOLD_S:
            record = logger.makeRecord("teamteam", logging.WARNING, "", 0,
                f"AI chat summary slow: {total_latency:.2f}s (external: {ext_latency:.2f}s)", (), None)
            record.extra_data = log_extra
            logger.handle(record)
        else:
            record = logger.makeRecord("teamteam", logging.INFO, "", 0,
                f"AI chat summary latency: {total_latency:.2f}s (external: {ext_latency:.2f}s)", (), None)
            record.extra_data = log_extra
            logger.handle(record)

        # Post-response disconnect check — count wasted AI calls
        if await request.is_disconnected():
            ai_chat_disconnect_total.inc()
            logger.warning(f"AI chat summary: client disconnected after response (room_id={room_id})")

        return AIPromptResponse(prompt=response.text)
    except Exception as e:
        total_latency = time.time() - endpoint_start
        ai_chat_summary_latency.observe(total_latency)
        logger.error(f"AI prompt generation failed after {total_latency:.2f}s: {e}")
        raise HTTPException(status_code=502, detail=f"AI 프롬프트 생성에 실패했습니다: {str(e)}")
