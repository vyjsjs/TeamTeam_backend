"""User profile routes: view and update my profile."""

from fastapi import APIRouter, Depends, HTTPException, status
from app.dependencies import get_current_user
from app.core.supabase import get_supabase
from app.schemas.user import UserProfileWithStats, UserUpdateRequest

router = APIRouter(prefix="/api/users", tags=["Users"])


@router.get("/me", response_model=UserProfileWithStats)
async def get_my_profile(current_user: dict = Depends(get_current_user)):
    """마이페이지 조회 — 프로필 정보 및 평가 통계."""
    db = get_supabase()
    user_id = current_user["id"]

    # Get evaluation statistics
    evals = (
        db.table("evaluation")
        .select("score_participation, score_responsibility, score_communication, score_collaboration, score_creativity")
        .eq("evaluatee_id", user_id)
        .execute()
    )

    stats = {}
    if evals.data:
        total = len(evals.data)
        stats = {
            "avg_participation": round(sum(e["score_participation"] for e in evals.data) / total, 2),
            "avg_responsibility": round(sum(e["score_responsibility"] for e in evals.data) / total, 2),
            "avg_communication": round(sum(e["score_communication"] for e in evals.data) / total, 2),
            "avg_collaboration": round(sum(e["score_collaboration"] for e in evals.data) / total, 2),
            "avg_creativity": round(sum(e["score_creativity"] for e in evals.data) / total, 2),
            "total_evaluations": total,
        }

    return UserProfileWithStats(**current_user, **stats)


@router.patch("/me", response_model=dict)
async def update_my_profile(
    body: UserUpdateRequest,
    current_user: dict = Depends(get_current_user),
):
    """내 정보 수정 — 프로필 이미지, 자기소개, 거주지역 등."""
    db = get_supabase()
    update_data = body.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="수정할 항목을 입력해주세요.",
        )

    result = (
        db.table("user")
        .update(update_data)
        .eq("id", current_user["id"])
        .execute()
    )

    return {"message": "프로필이 수정되었습니다.", "updated_fields": list(update_data.keys())}
