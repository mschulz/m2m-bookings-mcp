# app/database.py

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Session

from config import get_settings


class Base(DeclarativeBase):
    pass


engine = create_engine(
    get_settings().SQLALCHEMY_DATABASE_URI,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
