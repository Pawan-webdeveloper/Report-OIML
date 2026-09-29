from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # App
    APP_NAME: str = "NAWI Type-Evaluation Portal (OIML R 76)"
    ENV: str = "dev"                    # dev | prod
    API_PREFIX: str = "/api"

    # DB — dev: SQLite | prod: postgresql+psycopg://user:pass@host/nawi
    DATABASE_URL: str = "sqlite:///./nawi.db"

    # Auth (Phase 4)
    JWT_SECRET: str = "dev-secret-change-me"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_MINUTES: int = 15
    REFRESH_TOKEN_DAYS: int = 7

    # Ruleset — Golden Design Rule #2: rules = data, not code
    RULESET_ID: str = "oiml-r76-2006"

    # Files (Phase 8)
    UPLOAD_DIR: str = "./uploads"


@lru_cache
def get_settings() -> Settings:
    return Settings()