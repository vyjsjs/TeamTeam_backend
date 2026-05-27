"""Auth request/response schemas."""

from pydantic import BaseModel, EmailStr,field_validator


class SignUpRequest(BaseModel):
    email: EmailStr
    password: str
    name: str
    department: str | None = None
    student_id: str | None = None
    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("비밀번호는 8자 이상이어야 합니다.")
        if not any(c.isdigit() for c in v):
            raise ValueError("비밀번호에 숫자가 포함되어야 합니다.")
        if not any(c.isalpha() for c in v):
            raise ValueError("비밀번호에 영문자가 포함되어야 합니다.")
        return v

    @field_validator("name")
    @classmethod
    def name_length(cls, v: str) -> str:
        if len(v.strip()) < 1 or len(v) > 50:
            raise ValueError("이름은 1~50자여야 합니다.")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    name: str
