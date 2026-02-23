# app/database/missing_locations.py

from app.database import SessionLocal
from app.daos.booking import booking_dao
from app.services.email_service import send_missing_location_email
from config import get_settings


def main():
    db = SessionLocal()
    try:
        res = booking_dao.get_bookings_missing_locations(db)
        number_locations = len(res)

        print(f"Locations missing = {number_locations}")

        if res:
            missing = {item.postcode for item in res if item.postcode is not None}
            missing_list = sorted(missing)
            number_postcodes = len(missing_list)

            print(f"Postcodes missing = {number_postcodes}")

            settings = get_settings()
            to_addr = settings.MISSING_LOCATION_EMAIL
            msg = str(missing_list)
            send_missing_location_email(to_addr, msg, number_locations, number_postcodes)
    finally:
        db.close()


if __name__ == "__main__":
    main()
