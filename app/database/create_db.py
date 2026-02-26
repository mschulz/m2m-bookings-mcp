# app/database/create_db.py

import asyncio

from sqlmodel import SQLModel

from app.core.database import engine

# Import all models so they are registered with SQLModel.metadata
from app.models.booking import Booking  # noqa: F401
from app.models.customer import Customer  # noqa: F401


async def _create_tables():
    """Create all tables using the async engine."""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    await engine.dispose()
    print("Database tables created.")


def main():
    """Create the initial database. Should only call this once."""
    asyncio.run(_create_tables())


if __name__ == "__main__":
    main()
