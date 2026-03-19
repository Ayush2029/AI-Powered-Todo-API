from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # DATABASE_URL injected by Render automatically via fromDatabase.
    # No default — missing value raises ValidationError at startup.
    DATABASE_URL: str

    # Free Groq API key — get one at https://console.groq.com (no credit card)
    GROQ_API_KEY: str
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
