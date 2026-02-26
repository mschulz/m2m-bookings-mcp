"""SQLModel engine, session factory, and FastAPI database dependency."""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlmodel import Session

from app.core.config import get_settings


engine = create_engine(
    get_settings().SQLALCHEMY_DATABASE_URI,
    pool_pre_ping=True,
    pool_size=3,
    max_overflow=2,
    pool_timeout=10,
    pool_recycle=1800,
)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a database session."""
    with Session(engine) as session:
        yield session
