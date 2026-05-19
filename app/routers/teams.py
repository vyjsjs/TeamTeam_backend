"""Team management routes."""

import secrets
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status
from app.dependencies import get_current_user
from app.core.supabase import get_supabase
from app.schemas.team import (
    TeamCreateRequest,
    TeamJoinRequest,
    TeamResponse,
    TeamListItem,
    TeamDashboard,
    TeamStatusUpdate,
)

router = APIRouter(prefix="/api/teams", tags=["Teams"])


def _generate_invite_code() -> str:
    """Generate a random 8-character alphanumeric invite code."""
    return secrets.token_urlsafe(6)[:8].upper()


@router.post("", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
async def create_team(
    body: TeamCreateRequest,
    current_user: dict = Depends(get_current_user),
):
    """팀 생성 — 팀명, 과목, 마감일 입력. 초대 코드 생성 및 생성자를 팀장으로 설정."""
    db = get_supabase()

    invite_code = _generate_invite_code()
    team_data = {
        "team_name": body.team_name,
        "subject_name": body.subject_name,
        "deadline": body.deadline.isoformat() if body.deadline else None,
        "invite_code": invite_code,
        "leader_id": current_user["id"],
    }

    result = db.table("team").insert(team_data).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="팀 생성에 실패했습니다.")

    team = result.data[0]

    # Auto-add creator as team member
    db.table("team_member").insert({
        "team_id": team["id"],
        "user_id": current_user["id"],
    }).execute()

    return TeamResponse(**team)


@router.post("/join", response_model=dict)
async def join_team(
    body: TeamJoinRequest,
    current_user: dict = Depends(get_current_user),
):
    """팀 참여 — 초대 코드 입력으로 팀 가입."""
    db = get_supabase()

    # Find team by invite code
    team_result = (
        db.table("team")
        .select("id, team_name, status")
        .eq("invite_code", body.invite_code)
        .execute()
    )
    if not team_result.data:
        raise HTTPException(status_code=404, detail="유효하지 않은 초대 코드입니다.")

    team = team_result.data[0]
    if team["status"] == "종료":
        raise HTTPException(status_code=400, detail="종료된 프로젝트에는 참여할 수 없습니다.")

    # Check if already a member
    existing = (
        db.table("team_member")
        .select("id")
        .eq("team_id", team["id"])
        .eq("user_id", current_user["id"])
        .execute()
    )
    if existing.data:
        raise HTTPException(status_code=409, detail="이미 해당 팀에 참여중입니다.")

    # Add as member
    db.table("team_member").insert({
        "team_id": team["id"],
        "user_id": current_user["id"],
    }).execute()

    return {"message": f"'{team['team_name']}' 팀에 참여했습니다.", "team_id": team["id"]}


@router.get("", response_model=list[TeamListItem])
async def list_my_teams(current_user: dict = Depends(get_current_user)):
    """내 팀 목록 조회 — 사용자가 속한 모든 팀 (헤더 드롭다운용)."""
    db = get_supabase()

    # Get team IDs the user belongs to
    memberships = (
        db.table("team_member")
        .select("team_id")
        .eq("user_id", current_user["id"])
        .execute()
    )

    if not memberships.data:
        return []

    team_ids = [m["team_id"] for m in memberships.data]

    # Get team info
    teams = (
        db.table("team")
        .select("*")
        .in_("id", team_ids)
        .execute()
    )

    result = []
    for team in teams.data:
        # Count members
        members = (
            db.table("team_member")
            .select("id", count="exact")
            .eq("team_id", team["id"])
            .execute()
        )
        member_count = members.count or 0

        # Calculate progress (Done tasks / Total tasks)
        all_tasks = db.table("task").select("status").eq("team_id", team["id"]).execute()
        total_tasks = len(all_tasks.data) if all_tasks.data else 0
        done_tasks = len([t for t in all_tasks.data if t["status"] == "Done"]) if all_tasks.data else 0
        progress = round((done_tasks / total_tasks) * 100, 1) if total_tasks > 0 else 0.0

        result.append(TeamListItem(
            id=team["id"],
            team_name=team["team_name"],
            subject_name=team.get("subject_name"),
            status=team["status"],
            deadline=team.get("deadline"),
            leader_id=team["leader_id"],
            member_count=member_count,
            progress=progress,
        ))

    return result


@router.get("/{team_id}", response_model=TeamDashboard)
async def get_team_dashboard(
    team_id: int,
    current_user: dict = Depends(get_current_user),
):
    """팀 메인 대시보드 — 요약 정보 (팀원, 최신 공지, 오늘 일정, 진행률)."""
    db = get_supabase()

    # Verify membership
    membership = (
        db.table("team_member")
        .select("id")
        .eq("team_id", team_id)
        .eq("user_id", current_user["id"])
        .execute()
    )
    if not membership.data:
        raise HTTPException(status_code=403, detail="해당 팀의 멤버가 아닙니다.")

    # Team info
    team_result = db.table("team").select("*").eq("id", team_id).single().execute()
    if not team_result.data:
        raise HTTPException(status_code=404, detail="팀을 찾을 수 없습니다.")

    team = team_result.data

    # Members with user info
    members_result = (
        db.table("team_member")
        .select("user_id, joined_at, user:user_id(id, name, email, profile_image_url)")
        .eq("team_id", team_id)
        .execute()
    )
    members = members_result.data or []

    # Latest notice
    notice_result = (
        db.table("notice")
        .select("*")
        .eq("team_id", team_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    latest_notice = notice_result.data[0] if notice_result.data else None

    # Today's tasks
    today = date.today().isoformat()
    today_tasks_result = (
        db.table("task")
        .select("*")
        .eq("team_id", team_id)
        .eq("due_date", today)
        .execute()
    )
    today_tasks = today_tasks_result.data or []

    # Progress
    all_tasks = db.table("task").select("status").eq("team_id", team_id).execute()
    total = len(all_tasks.data) if all_tasks.data else 0
    done = len([t for t in all_tasks.data if t["status"] == "Done"]) if all_tasks.data else 0
    progress = round((done / total) * 100, 1) if total > 0 else 0.0

    return TeamDashboard(
        team=TeamResponse(**team),
        members=members,
        latest_notice=latest_notice,
        today_tasks=today_tasks,
        progress=progress,
    )


@router.patch("/{team_id}/status", response_model=dict)
async def update_team_status(
    team_id: int,
    body: TeamStatusUpdate,
    current_user: dict = Depends(get_current_user),
):
    """팀 프로젝트 상태 변경 — 팀장 전용 (진행중 → 종료)."""
    db = get_supabase()

    # Verify leader
    team = db.table("team").select("leader_id").eq("id", team_id).single().execute()
    if not team.data:
        raise HTTPException(status_code=404, detail="팀을 찾을 수 없습니다.")

    if team.data["leader_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="팀장만 상태를 변경할 수 있습니다.")

    if body.status not in ("진행중", "종료"):
        raise HTTPException(status_code=400, detail="유효하지 않은 상태입니다. ('진행중' 또는 '종료')")

    db.table("team").update({"status": body.status}).eq("id", team_id).execute()

    return {"message": f"프로젝트 상태가 '{body.status}'으로 변경되었습니다."}
