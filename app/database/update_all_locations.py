# app/database/update_all_locations.py

from app.database import SessionLocal
from app.models.booking import Booking
from app.services.locations import get_location


def main():
    db = SessionLocal()
    try:
        res = db.query(Booking).all()

        print(f"booking ids to sort out = {len(res)}")

        for item in res:
            postcode = item.postcode
            location = get_location(postcode)

            print(f"{postcode} => {location}")

            item.location = location
            db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    main()
