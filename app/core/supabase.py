"""Supabase client singleton for database operations."""

from supabase import create_client, Client
from app.core.config import get_settings

_client: Client | None = None


def get_supabase() -> Client:
    """Return a singleton Supabase client."""
    global _client
    if _client is None:
        settings = get_settings()
        _client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    return _client
