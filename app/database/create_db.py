# app/database/create_db.py

from sqlmodel import SQLModel

from app.core.database import engine

# Import all models so they are registered with SQLModel.metadata
from app.models.booking import Booking  # noqa: F401
from app.models.customer import Customer  # noqa: F401


def main():
    """Create the initial database. Should only call this once."""
    SQLModel.metadata.create_all(bind=engine)
    print("Database tables created.")


if __name__ == "__main__":
    main()
