from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import get_settings

settings = get_settings()

# Ensure the directory exists for SQLite databases (e.g. on Render persistent disk)
if settings.DATABASE_URL.startswith("sqlite"):
    from pathlib import Path

    db_path_str = settings.DATABASE_URL.replace("sqlite:///", "", 1)
    if db_path_str:
        db_dir = Path(db_path_str).parent
        db_dir.mkdir(parents=True, exist_ok=True)

# This flag is required for SQLite with FastAPI threads
_connect_args = (
    {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}
)

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=_connect_args,
    pool_pre_ping=True,
)

# FK enforcement (ON DELETE CASCADE etc.) is OFF by DEFAULT in SQLite —
# it must be turned ON for data integrity (native on PG).
if settings.DATABASE_URL.startswith("sqlite"):

    @event.listens_for(engine, "connect")
    def _sqlite_fk_pragma(dbapi_conn, _record):
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA foreign_keys=ON")
        cur.close()


SessionLocal = sessionmaker(
    bind=engine, autoflush=False, autocommit=False, expire_on_commit=False
)


class Base(DeclarativeBase):
    """All models inherit from this (full schema in doc §4)."""


def get_db():
    """FastAPI dependency — one request = one DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()