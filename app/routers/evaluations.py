"""Evaluation (peer review) routes."""

from fastapi import APIRouter, Depends, HTTPException
from app.dependencies import get_current_user
from app.core.supabase import get_supabase
from app.schemas.evaluation import EvaluationCreateRequest, EvaluationResponse, EvalStatusItem

router = APIRouter(tags=["Evaluations"])


def _verify_member(db, team_id: int, user_id: int):
    r = db.table("team_member").select("id").eq("team_id", team_id).eq("user_id", user_id).execute()
    if not r.data:
        raise HTTPException(status_code=403, detail="해당 팀의 멤버가 아닙니다.")


@router.post("/api/teams/{team_id}/evaluations", response_model=EvaluationResponse, status_code=201)
async def submit_evaluation(team_id: int, body: EvaluationCreateRequest, current_user: dict = Depends(get_current_user)):
    """상호평가 제출."""
    db = get_supabase()
    _verify_member(db, team_id, current_user["id"])

    if body.evaluatee_id == current_user["id"]:
        raise HTTPException(status_code=400, detail="자기 자신을 평가할 수 없습니다.")

    # Check evaluatee is also a member
    _verify_member(db, team_id, body.evaluatee_id)

    # Check for duplicate
    existing = db.table("evaluation").select("id").eq("team_id", team_id).eq("evaluator_id", current_user["id"]).eq("evaluatee_id", body.evaluatee_id).execute()
    if existing.data:
        raise HTTPException(status_code=409, detail="이미 해당 팀원을 평가했습니다.")

    eval_data = {
        "team_id": team_id,
        "evaluator_id": current_user["id"],
        "evaluatee_id": body.evaluatee_id,
        "score_participation": body.score_participation,
        "score_responsibility": body.score_responsibility,
        "score_communication": body.score_communication,
        "score_collaboration": body.score_collaboration,
        "score_creativity": body.score_creativity,
        "comment": body.comment,
    }

    result = db.table("evaluation").insert(eval_data).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="평가 제출에 실패했습니다.")

    return EvaluationResponse(**result.data[0])


@router.get("/api/teams/{team_id}/members/eval-status", response_model=list[EvalStatusItem])
async def get_eval_status(team_id: int, current_user: dict = Depends(get_current_user)):
    """평가 대상자 목록 — 평가 완료/미완료 구분."""
    db = get_supabase()
    _verify_member(db, team_id, current_user["id"])

    # Get all members except self
    members = db.table("team_member").select("user_id, user:user_id(id, name)").eq("team_id", team_id).execute()

    # Get my evaluations for this team
    my_evals = db.table("evaluation").select("evaluatee_id").eq("team_id", team_id).eq("evaluator_id", current_user["id"]).execute()
    evaluated_ids = {e["evaluatee_id"] for e in my_evals.data or []}

    result = []
    for m in members.data or []:
        user = m.get("user", {})
        uid = user.get("id", m["user_id"])
        if uid == current_user["id"]:
            continue
        result.append(EvalStatusItem(
            user_id=uid,
            user_name=user.get("name", ""),
            evaluated=uid in evaluated_ids,
        ))
    return result
