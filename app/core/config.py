"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Supabase
    SUPABASE_URL: str
    SUPABASE_KEY: str  # anon key (publishable)
    SUPABASE_SERVICE_KEY: str = ""  # service role key (optional, for admin ops)


    # Gemini (for AI schedule recommendations & chat summary)
    GEMINI_API_KEY: str = ""

    # App
    APP_NAME: str = "TeamTeam Backend"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True

    # CORS
    CORS_ORIGINS: str = "*"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


@lru_cache()
def get_settings() -> Settings:
    return Settings()
