"""Task management routes."""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.dependencies import get_current_user
from app.core.supabase import get_supabase
from app.schemas.task import TaskCreateRequest, TaskUpdateRequest, TaskResponse

router = APIRouter(tags=["Tasks"])


def _verify_team_member(db, team_id: int, user_id: int):
    result = (
        db.table("team_member")
        .select("id")
        .eq("team_id", team_id)
        .eq("user_id", user_id)
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=403, detail="해당 팀의 멤버가 아닙니다.")


@router.get("/api/teams/{team_id}/tasks", response_model=list[TaskResponse])
async def list_tasks(
    team_id: int,
    mine_only: bool = Query(False, description="내 업무만 보기"),
    current_user: dict = Depends(get_current_user),
):
    """전체 일정(업무) 조회 — 캘린더용. mine_only=true이면 본인 업무만."""
    db = get_supabase()
    _verify_team_member(db, team_id, current_user["id"])

    query = db.table("task").select("*, assignee:assignee_id(name)").eq("team_id", team_id)

    if mine_only:
        query = query.eq("assignee_id", current_user["id"])

    tasks = query.order("due_date").execute()

    result = []
    for t in tasks.data or []:
        assignee_name = t.get("assignee", {}).get("name") if t.get("assignee") else None
        result.append(TaskResponse(
            id=t["id"],
            team_id=t["team_id"],
            assignee_id=t.get("assignee_id"),
            assignee_name=assignee_name,
            task_name=t["task_name"],
            due_date=t.get("due_date"),
            status=t["status"],
            created_at=t.get("created_at"),
            updated_at=t.get("updated_at"),
        ))
    return result


@router.post("/api/teams/{team_id}/tasks", response_model=TaskResponse, status_code=201)
async def create_task(
    team_id: int,
    body: TaskCreateRequest,
    current_user: dict = Depends(get_current_user),
):
    """개인 업무 추가 — 내 업무만 생성 가능 (assignee = 본인)."""
    db = get_supabase()
    _verify_team_member(db, team_id, current_user["id"])

    task_data = {
        "team_id": team_id,
        "assignee_id": current_user["id"],
        "task_name": body.task_name,
        "due_date": body.due_date.isoformat() if body.due_date else None,
    }

    result = db.table("task").insert(task_data).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="업무 생성에 실패했습니다.")

    t = result.data[0]
    return TaskResponse(
        id=t["id"],
        team_id=t["team_id"],
        assignee_id=t.get("assignee_id"),
        assignee_name=current_user["name"],
        task_name=t["task_name"],
        due_date=t.get("due_date"),
        status=t["status"],
        created_at=t.get("created_at"),
        updated_at=t.get("updated_at"),
    )


@router.patch("/api/tasks/{task_id}", response_model=dict)
async def update_task(
    task_id: int,
    body: TaskUpdateRequest,
    current_user: dict = Depends(get_current_user),
):
    """업무 상태 수정 — 본인 업무만 수정 가능."""
    db = get_supabase()

    # Check task ownership
    task = db.table("task").select("assignee_id, team_id").eq("id", task_id).single().execute()
    if not task.data:
        raise HTTPException(status_code=404, detail="업무를 찾을 수 없습니다.")

    if task.data["assignee_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="본인의 업무만 수정할 수 있습니다.")

    update_data = body.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="수정할 항목을 입력해주세요.")

    # Validate status
    if "status" in update_data and update_data["status"] not in ("To do", "In progress", "Done"):
        raise HTTPException(status_code=400, detail="유효하지 않은 상태입니다. ('To do', 'In progress', 'Done')")

    if "due_date" in update_data and update_data["due_date"]:
        update_data["due_date"] = update_data["due_date"].isoformat()

    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()

    db.table("task").update(update_data).eq("id", task_id).execute()

    return {"message": "업무가 수정되었습니다."}
