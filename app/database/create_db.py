# app/database/create_db.py

from app.database import engine, Base

# Import all models so they are registered with Base.metadata
from app.models.booking import Booking, Reservation, SalesReservation  # noqa: F401
from app.models.customer import Customer  # noqa: F401


def main():
    """Create the initial database. Should only call this once."""
    Base.metadata.create_all(bind=engine)
    print("Database tables created.")


if __name__ == "__main__":
    main()
