"""Security utilities for demo ID auth."""

def hash_password(password: str) -> str:
    """Return plain text password for demo."""
    return password


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plain text password for demo."""
    return plain_password == hashed_password


def create_access_token(data: dict) -> str:
    """Create a dummy token that is just the user_id."""
    return str(data.get("user_id", ""))


def decode_access_token(token: str) -> dict | None:
    """Decode a dummy token by returning the user_id."""
    try:
        return {"user_id": int(token)}
    except ValueError:
        return None
