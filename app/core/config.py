from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # DATABASE_URL must be injected by Render (fromDatabase) or set in .env locally.
    # No default — missing value raises ValidationError at startup (intentional).
    DATABASE_URL: str

    # Get a FREE Gemini API key at https://aistudio.google.com — no credit card needed.
    GEMINI_API_KEY: str
    GEMINI_MODEL: str = "gemini-2.5-flash-preview-04-17"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
