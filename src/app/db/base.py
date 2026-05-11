from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session

from app.config.settings import DATABASE_URL, ensure_directories_exist


class Base(DeclarativeBase):
    pass


def _get_connect_args() -> dict:
    """
    SQLite needs check_same_thread=False when used with Streamlit.
    Other databases do not need this argument.
    """
    if DATABASE_URL.startswith("sqlite"):
        return {"check_same_thread": False}

    return {}


ensure_directories_exist()

engine = create_engine(
    DATABASE_URL,
    connect_args=_get_connect_args(),
    echo=False,
)
if DATABASE_URL.startswith("sqlite"):

    @event.listens_for(engine, "connect")
    def enable_sqlite_foreign_keys(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Provides a database session and closes it automatically.

    Usage:
        with get_db_session() as db:
            ...
    """
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()

