"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """MedLens application settings.

    Loaded from .env file and environment variables.
    No PHI or secrets should ever appear in defaults.
    """

    app_name: str = "MedLens"
    app_env: str = "development"
    log_level: str = "INFO"

    # Database
    database_url: str = "sqlite:///./medlens.db"

    # CORS — React dev server
    cors_origins: list[str] = ["http://localhost:5173"]

    # LLM (not used in Phase 1, but configured for later)
    llm_provider: str = "gemini"
    llm_api_key: str = ""
    llm_model: str = "gemini-2.0-flash"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


# Singleton — import this everywhere
settings = Settings()
