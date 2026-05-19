"""Reference room routes."""

from fastapi import APIRouter, Depends, HTTPException
from app.dependencies import get_current_user
from app.core.supabase import get_supabase
from app.schemas.reference import ReferenceCreateRequest, ReferenceResponse

router = APIRouter(tags=["References"])


def _verify_member(db, team_id: int, user_id: int):
    r = db.table("team_member").select("id").eq("team_id", team_id).eq("user_id", user_id).execute()
    if not r.data:
        raise HTTPException(status_code=403, detail="해당 팀의 멤버가 아닙니다.")


@router.get("/api/teams/{team_id}/references", response_model=list[ReferenceResponse])
async def list_references(team_id: int, current_user: dict = Depends(get_current_user)):
    db = get_supabase()
    _verify_member(db, team_id, current_user["id"])
    refs = db.table("reference_room").select("*, uploader:uploader_id(name)").eq("team_id", team_id).order("created_at", desc=True).execute()
    result = []
    for r in refs.data or []:
        uname = r.get("uploader", {}).get("name") if r.get("uploader") else None
        result.append(ReferenceResponse(id=r["id"], team_id=r["team_id"], uploader_id=r["uploader_id"], uploader_name=uname, file_name=r["file_name"], file_url=r["file_url"], created_at=r.get("created_at")))
    return result


@router.post("/api/teams/{team_id}/references", response_model=ReferenceResponse, status_code=201)
async def upload_reference(team_id: int, body: ReferenceCreateRequest, current_user: dict = Depends(get_current_user)):
    db = get_supabase()
    _verify_member(db, team_id, current_user["id"])
    ref_data = {"team_id": team_id, "uploader_id": current_user["id"], "file_name": body.file_name, "file_url": body.file_url}
    result = db.table("reference_room").insert(ref_data).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="자료 업로드에 실패했습니다.")
    r = result.data[0]
    return ReferenceResponse(id=r["id"], team_id=r["team_id"], uploader_id=r["uploader_id"], uploader_name=current_user["name"], file_name=r["file_name"], file_url=r["file_url"], created_at=r.get("created_at"))


@router.delete("/api/references/{ref_id}", response_model=dict)
async def delete_reference(ref_id: int, current_user: dict = Depends(get_current_user)):
    db = get_supabase()
    ref = db.table("reference_room").select("uploader_id").eq("id", ref_id).single().execute()
    if not ref.data:
        raise HTTPException(status_code=404, detail="자료를 찾을 수 없습니다.")
    if ref.data["uploader_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="본인이 업로드한 자료만 삭제할 수 있습니다.")
    db.table("reference_room").delete().eq("id", ref_id).execute()
    return {"message": "자료가 삭제되었습니다."}
