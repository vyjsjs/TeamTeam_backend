"""Notice routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from app.dependencies import get_current_user
from app.core.supabase import get_supabase
from app.schemas.notice import NoticeCreateRequest, NoticeResponse

router = APIRouter(tags=["Notices"])


def _verify_team_member(db, team_id: int, user_id: int):
    """Verify that the user is a member of the team."""
    result = (
        db.table("team_member")
        .select("id")
        .eq("team_id", team_id)
        .eq("user_id", user_id)
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=403, detail="해당 팀의 멤버가 아닙니다.")


@router.get("/api/teams/{team_id}/notices", response_model=list[NoticeResponse])
async def list_notices(
    team_id: int,
    current_user: dict = Depends(get_current_user),
):
    """공지사항 목록 조회 — 팀장 공지와 팀원 공지 구분."""
    db = get_supabase()
    _verify_team_member(db, team_id, current_user["id"])

    notices = (
        db.table("notice")
        .select("*, author:author_id(name)")
        .eq("team_id", team_id)
        .order("created_at", desc=True)
        .execute()
    )

    result = []
    for n in notices.data or []:
        author_name = n.get("author", {}).get("name") if n.get("author") else None
        result.append(NoticeResponse(
            id=n["id"],
            team_id=n["team_id"],
            author_id=n["author_id"],
            author_name=author_name,
            title=n["title"],
            content=n.get("content"),
            is_leader_notice=n.get("is_leader_notice", False),
            created_at=n.get("created_at"),
        ))
    return result


@router.post("/api/teams/{team_id}/notices", response_model=NoticeResponse, status_code=201)
async def create_notice(
    team_id: int,
    body: NoticeCreateRequest,
    current_user: dict = Depends(get_current_user),
):
    """공지사항 작성 — 팀장 여부에 따라 is_leader_notice 자동 설정."""
    db = get_supabase()
    _verify_team_member(db, team_id, current_user["id"])

    # Check if user is leader
    team = db.table("team").select("leader_id").eq("id", team_id).single().execute()
    is_leader = team.data and team.data["leader_id"] == current_user["id"]

    notice_data = {
        "team_id": team_id,
        "author_id": current_user["id"],
        "title": body.title,
        "content": body.content,
        "is_leader_notice": is_leader,
    }

    result = db.table("notice").insert(notice_data).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="공지사항 작성에 실패했습니다.")

    n = result.data[0]
    return NoticeResponse(
        id=n["id"],
        team_id=n["team_id"],
        author_id=n["author_id"],
        author_name=current_user["name"],
        title=n["title"],
        content=n.get("content"),
        is_leader_notice=n.get("is_leader_notice", False),
        created_at=n.get("created_at"),
    )


@router.get("/api/notices/{notice_id}", response_model=NoticeResponse)
async def get_notice_detail(
    notice_id: int,
    current_user: dict = Depends(get_current_user),
):
    """공지사항 상세 조회."""
    db = get_supabase()

    notice = (
        db.table("notice")
        .select("*, author:author_id(name)")
        .eq("id", notice_id)
        .single()
        .execute()
    )
    if not notice.data:
        raise HTTPException(status_code=404, detail="공지사항을 찾을 수 없습니다.")

    n = notice.data
    _verify_team_member(db, n["team_id"], current_user["id"])

    author_name = n.get("author", {}).get("name") if n.get("author") else None
    return NoticeResponse(
        id=n["id"],
        team_id=n["team_id"],
        author_id=n["author_id"],
        author_name=author_name,
        title=n["title"],
        content=n.get("content"),
        is_leader_notice=n.get("is_leader_notice", False),
        created_at=n.get("created_at"),
    )
