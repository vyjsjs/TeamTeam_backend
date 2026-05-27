"""Security utilities for demo ID auth."""
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from passlib.context import CryptContext
from app.core.config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)

def hash_password(password: str) -> str:
    """Return plain text password for demo."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plain text password for demo."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict) -> str:
    """Create a dummy token that is just the user_id."""
    settings = get_settings()
    payload = data.copy()
    payload["exp"] = datetime.now(timezone.utc) + timedelta(minutes=15)
    return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")
    

def create_refresh_token(data: dict) -> str:
    settings = get_settings()
    payload = data.copy()
    payload["exp"] = datetime.now(timezone.utc) + timedelta(days=3)
    return jwt.encode(payload, settings.REFRESH_SECRET, algorithm="HS256")

def decode_access_token(token: str) -> dict | None:
    settings = get_settings()
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
    except JWTError:
        return None

def decode_refresh_token(token: str) -> dict | None:
    settings = get_settings()
    try:
        return jwt.decode(token, settings.REFRESH_SECRET, algorithms=["HS256"])
    except JWTError:
        return None
