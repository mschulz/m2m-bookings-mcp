# app/database/update_locations.py

from app.database import SessionLocal
from app.daos.booking import booking_dao
from app.utils.locations import get_location
from app.utils.email_service import send_updated_locations_email
from config import get_settings


def main():
    db = SessionLocal()
    try:
        res = booking_dao.get_bookings_missing_locations(db)
        number_locations = len(res)

        print(f"Bookings with no locations to update = {number_locations}")

        missing = 0
        updated = 0
        postcodes_missing = set()

        if res:
            for item in res:
                postcode = item.postcode
                location = get_location(postcode)

                if location is None:
                    missing += 1
                    if postcode not in postcodes_missing:
                        postcodes_missing.add(postcode)
                else:
                    updated += 1
                    item.location = location
                    db.commit()
        print(
            f"Locations to update:{number_locations} Missing={missing} Updated={updated}"
        )
        settings = get_settings()
        to_addr = settings.MISSING_LOCATION_EMAIL
        send_updated_locations_email(
            to_addr, number_locations, updated, missing, len(postcodes_missing)
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()
