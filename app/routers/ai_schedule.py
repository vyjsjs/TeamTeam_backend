"""AI Schedule recommendation routes (leader-only)."""

import json
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from app.dependencies import get_current_user
from app.core.supabase import get_supabase
from app.core.config import get_settings
from app.schemas.ai_schedule import (
    AIScheduleRequest,
    AIScheduleTaskItem,
    AISessionResponse,
    AIConfirmRequest,
)

router = APIRouter(tags=["AI Schedule"])
logger = logging.getLogger("teamteam")


def _verify_leader(db, team_id: int, user_id: int):
    """Verify the user is the team leader."""
    team = db.table("team").select("leader_id").eq("id", team_id).single().execute()
    if not team.data:
        raise HTTPException(status_code=404, detail="팀을 찾을 수 없습니다.")
    if team.data["leader_id"] != user_id:
        raise HTTPException(status_code=403, detail="팀장만 사용할 수 있는 기능입니다.")


async def _call_openai_schedule(goal: str, deadline: str, tasks: list[str]) -> list[dict]:
    """Call OpenAI API to generate schedule recommendations.

    Falls back to a simple even-distribution algorithm if the API key is not configured.
    """
    settings = get_settings()

    if not settings.GEMINI_API_KEY:
        # Fallback: simple even distribution when no API key
        from datetime import date, timedelta

        deadline_date = date.fromisoformat(deadline)
        today = date.today()
        total_days = (deadline_date - today).days
        if total_days <= 0:
            total_days = len(tasks)

        days_per_task = max(1, total_days // len(tasks))
        result = []
        current = today
        for task_name in tasks:
            end = current + timedelta(days=days_per_task)
            if end > deadline_date:
                end = deadline_date
            result.append({
                "task_name": task_name,
                "start_date": current.isoformat(),
                "due_date": end.isoformat(),
            })
            current = end
        return result

    import google.generativeai as genai
    genai.configure(api_key=settings.GEMINI_API_KEY)

    prompt = f"""당신은 프로젝트 일정 관리 전문가입니다.
다음 팀 프로젝트의 업무 일정을 추천해주세요.

최종 목표: {goal}
마감일: {deadline}
해야 할 일 목록:
{chr(10).join(f"- {t}" for t in tasks)}

오늘 날짜: {date.today().isoformat()}

각 업무의 시작일과 마감일을 추천해주세요. 선후관계가 필요한 업무는 그에 맞게 날짜를 지정해주세요.
반드시 아래 JSON 형식으로만 응답하세요. 다른 설명은 제외하고 순수 JSON 배열만 출력하세요:

[
  {{"task_name": "업무명", "start_date": "YYYY-MM-DD", "due_date": "YYYY-MM-DD"}},
  ...
]
"""

    start_time = datetime.now(timezone.utc)
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                temperature=0.3
            )
        )
        latency = (datetime.now(timezone.utc) - start_time).total_seconds()
        logger.info(f"AI schedule API latency: {latency:.2f}s")

        content = response.text
        data = json.loads(content)
        if isinstance(data, dict):
            data = data.get("tasks", data.get("schedule", []))
        return data

    except Exception as e:
        latency = (datetime.now(timezone.utc) - start_time).total_seconds()
        logger.error(f"AI schedule API failed after {latency:.2f}s: {e}")
        raise HTTPException(status_code=502, detail=f"AI 스케줄 생성에 실패했습니다: {str(e)}")


@router.post("/api/teams/{team_id}/ai-sessions", response_model=AISessionResponse, status_code=201)
async def create_ai_session(
    team_id: int,
    body: AIScheduleRequest,
    current_user: dict = Depends(get_current_user),
):
    """AI 스케줄 추천 요청 — 팀장 전용.

    최종 목표, 마감일, 할 일 리스트를 전달하면 AI가 일정을 추천합니다.
    """
    db = get_supabase()
    _verify_leader(db, team_id, current_user["id"])

    if not body.tasks:
        raise HTTPException(status_code=400, detail="할 일 목록을 하나 이상 입력해주세요.")

    # Create session
    session_data = {
        "team_id": team_id,
        "goal": body.goal,
        "deadline": body.deadline.isoformat(),
    }
    session_result = db.table("ai_schedule_session").insert(session_data).execute()
    if not session_result.data:
        raise HTTPException(status_code=500, detail="세션 생성에 실패했습니다.")

    session = session_result.data[0]

    # Generate AI recommendations
    recommended = await _call_openai_schedule(body.goal, body.deadline.isoformat(), body.tasks)

    # Save AI tasks
    ai_tasks = []
    for item in recommended:
        task_data = {
            "session_id": session["id"],
            "task_name": item["task_name"],
            "start_date": item.get("start_date"),
            "due_date": item.get("due_date"),
        }
        result = db.table("ai_schedule_task").insert(task_data).execute()
        if result.data:
            ai_tasks.append(AIScheduleTaskItem(**result.data[0]))

    return AISessionResponse(
        id=session["id"],
        team_id=session["team_id"],
        goal=session["goal"],
        deadline=session["deadline"],
        status=session["status"],
        tasks=ai_tasks,
        created_at=session.get("created_at"),
    )


@router.get("/api/ai-sessions/{session_id}", response_model=AISessionResponse)
async def get_ai_session(
    session_id: int,
    current_user: dict = Depends(get_current_user),
):
    """AI 추천 일정 확인 — 팀장 전용."""
    db = get_supabase()

    session = db.table("ai_schedule_session").select("*").eq("id", session_id).single().execute()
    if not session.data:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")

    _verify_leader(db, session.data["team_id"], current_user["id"])

    tasks = (
        db.table("ai_schedule_task")
        .select("*")
        .eq("session_id", session_id)
        .order("start_date")
        .execute()
    )

    return AISessionResponse(
        id=session.data["id"],
        team_id=session.data["team_id"],
        goal=session.data["goal"],
        deadline=session.data["deadline"],
        status=session.data["status"],
        tasks=[AIScheduleTaskItem(**t) for t in tasks.data or []],
        created_at=session.data.get("created_at"),
    )


@router.post("/api/ai-sessions/{session_id}/confirm", response_model=dict)
async def confirm_ai_session(
    session_id: int,
    body: AIConfirmRequest,
    current_user: dict = Depends(get_current_user),
):
    """AI 일정 최종 확정 — 팀장이 수정 후 확인하면 Task 테이블에 일괄 등록."""
    db = get_supabase()

    session = db.table("ai_schedule_session").select("*").eq("id", session_id).single().execute()
    if not session.data:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")

    if session.data["status"] != "pending":
        raise HTTPException(status_code=400, detail="이미 처리된 세션입니다.")

    _verify_leader(db, session.data["team_id"], current_user["id"])

    # Create tasks in the Task table
    created_count = 0
    for item in body.tasks:
        task_data = {
            "team_id": session.data["team_id"],
            "task_name": item.task_name,
            "due_date": item.due_date.isoformat() if item.due_date else None,
        }
        db.table("task").insert(task_data).execute()
        created_count += 1

    # Update session status to confirmed
    db.table("ai_schedule_session").update({"status": "confirmed"}).eq("id", session_id).execute()

    return {
        "message": f"{created_count}개의 업무가 등록되었습니다.",
        "tasks_created": created_count,
    }
