"""Alembic environment — wired to app settings + models."""
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import JSON, Uuid, engine_from_config, pool

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from app.core.config import get_settings        # noqa: E402
from app.core.db import Base                    # noqa: E402
import app.models                               # noqa: F401,E402 — register models
from app.models._types import ExactNumeric      # noqa: E402

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# .env → Settings → alembic (single source of truth)
config.set_main_option("sqlalchemy.url", get_settings().DATABASE_URL)

target_metadata = Base.metadata


def render_item(type_, obj, autogen_context):
    """Render custom types cleanly in migration files."""
    if type_ == "type":
        if isinstance(obj, ExactNumeric):
            autogen_context.imports.add("from app.models._types import ExactNumeric")
            return f"ExactNumeric(precision={obj.precision}, scale={obj.scale})"
        if isinstance(obj, JSON):
            autogen_context.imports.add("from app.models._types import JSONType")
            return "JSONType()"
        if isinstance(obj, Uuid):
            autogen_context.imports.add("from sqlalchemy import Uuid")
            return "Uuid()"
    return False   # rest uses default rendering


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
        render_item=render_item,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,      # SQLite ALTER TABLE support
            render_item=render_item,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()