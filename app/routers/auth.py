"""Authentication routes: signup and login."""

from fastapi import APIRouter, HTTPException, status
from app.core.supabase import get_supabase
from app.core.security import hash_password, verify_password, create_access_token
from app.schemas.auth import SignUpRequest, LoginRequest, TokenResponse

router = APIRouter(prefix="/api/auth", tags=["Auth"])


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def signup(body: SignUpRequest):
    """회원가입 — 이메일, 비밀번호, 이름 등으로 계정 생성 후 토큰 발급."""
    db = get_supabase()

    # Check if email already exists
    existing = db.table("user").select("id").eq("email", body.email).execute()
    if existing.data:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="이미 가입된 이메일입니다.",
        )

    # Create user
    hashed = hash_password(body.password)
    user_data = {
        "email": body.email,
        "password": hashed,
        "name": body.name,
        "department": body.department,
        "student_id": body.student_id,
    }
    result = db.table("user").insert(user_data).execute()

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="회원가입에 실패했습니다.",
        )

    user = result.data[0]
    token = create_access_token({"user_id": user["id"], "email": user["email"]})

    return TokenResponse(
        access_token=token,
        user_id=user["id"],
        name=user["name"],
    )


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest):
    """로그인 — 이메일과 비밀번호로 인증 후 JWT 토큰 발급."""
    db = get_supabase()

    result = db.table("user").select("*").eq("email", body.email).execute()
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 올바르지 않습니다.",
        )

    user = result.data[0]
    if not verify_password(body.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 올바르지 않습니다.",
        )

    token = create_access_token({"user_id": user["id"], "email": user["email"]})

    return TokenResponse(
        access_token=token,
        user_id=user["id"],
        name=user["name"],
    )
