"""SQLModel engine, session factory, and FastAPI database dependency."""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlmodel import Session

from config import get_settings


engine = create_engine(
    get_settings().SQLALCHEMY_DATABASE_URI,
    pool_pre_ping=True,
)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a database session."""
    with Session(engine) as session:
        yield session
