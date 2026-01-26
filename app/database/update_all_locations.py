# app/database/update_all_locations.py


from app import create_app, db
from app.models import Booking
from app.locations import get_location


def main():
    app = create_app()

    with app.app_context():
        res = db.session.query(Booking).all()

        print(f"booking ids to sort out = {len(res)}")

        for item in res:
            postcode = item.postcode
            location = get_location(postcode)

            print(f"{postcode} => {location}")

            item.location = location
            db.session.commit()


if __name__ == "__main__":
    main()
