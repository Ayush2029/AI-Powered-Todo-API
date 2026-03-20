from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    DATABASE_URL: str
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
