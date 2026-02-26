"""SQLModel async engine, session factory, and FastAPI database dependency."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.core.config import get_settings


def _async_url(url: str) -> str:
    """Convert a postgresql:// URL to postgresql+asyncpg://."""
    return url.replace("postgresql://", "postgresql+asyncpg://", 1)


engine = create_async_engine(
    _async_url(get_settings().SQLALCHEMY_DATABASE_URI),
    pool_pre_ping=True,
    pool_size=3,
    max_overflow=2,
    pool_timeout=10,
    pool_recycle=1800,
)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an async database session."""
    async with async_session() as session:
        yield session
