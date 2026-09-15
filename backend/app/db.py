"""SQLite persistence via SQLModel.

One file database, gitignored (see .gitignore) like model weights and
converted datasets — every environment (dev, demo, deployment) has its
own. No migrations framework: this is early enough that `create_all` on
startup is sufficient; add Alembic when the schema needs to change under
real data instead of being wiped and recreated.
"""
from __future__ import annotations

from collections.abc import Generator

from sqlmodel import Session, SQLModel, create_engine

from app.config import DATABASE_PATH

DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(f"sqlite:///{DATABASE_PATH}", connect_args={"check_same_thread": False})


def init_db() -> None:
    # Imported here, not at module load, so every table module is
    # registered on SQLModel.metadata before create_all runs.
    from app.models import db_models  # noqa: F401

    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
