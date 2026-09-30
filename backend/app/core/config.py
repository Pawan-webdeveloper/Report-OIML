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
    # Comma-separated browser origins (Vite dev server). Same-origin SPA
    # deploys do not need extra entries.
    CORS_ORIGINS: str = "http://localhost:5173"

    # DB — dev: SQLite | prod: postgresql+psycopg://user:pass@host/nawi
    DATABASE_URL: str = "sqlite:///./nawi.db"

    # Auth — JWT (project.md §3.1: 15 min access, 7 day refresh)
    JWT_SECRET: str = "dev-secret-change-me"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_MINUTES: int = 15
    REFRESH_TOKEN_DAYS: int = 7

    # Auth — account lockout policy (brute-force protection)
    MAX_FAILED_LOGINS: int = 5
    ACCOUNT_LOCK_MINUTES: int = 15

    # Auth — open demo sign-in: any username/password is accepted; an unknown
    # username is auto-provisioned. Set ALLOW_ANY_LOGIN=false in production.
    ALLOW_ANY_LOGIN: bool = True

    # Auth — refresh cookie (httpOnly; secure must be True behind HTTPS in prod)
    REFRESH_COOKIE_NAME: str = "nawi_refresh"
    COOKIE_SECURE: bool = False

    # Ruleset — Golden Design Rule #2: rules = data, not code
    RULESET_ID: str = "oiml-r76-2006"

    # Files (Phase 8)
    UPLOAD_DIR: str = "./uploads"


@lru_cache
def get_settings() -> Settings:
    return Settings()