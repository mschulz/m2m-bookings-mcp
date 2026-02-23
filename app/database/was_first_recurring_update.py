# app/database/was_first_recurring_update.py

import sys
import logging

from sqlalchemy import exc

from app.database import SessionLocal
from app.models.booking import Booking
from .spreadsheet import Spreadsheet

logger = logging.getLogger(__name__)


def main():
    """Upload data to the database. Updates was_first_recurring from CSV."""

    print(sys.argv)

    commit_flag = False

    if len(sys.argv) == 3:
        filename = sys.argv[1]
        if sys.argv[2] == "-c":
            commit_flag = True
        else:
            print(f"Invalid flag: {sys.argv[2]}")
            sys.exit(1)
    elif len(sys.argv) == 2:
        filename = sys.argv[1]
        commit_flag = False
    else:
        print(f"Missing filename: {sys.argv}")
        sys.exit(1)

    print(f"{filename = } {commit_flag = }")

    db = SessionLocal()
    try:
        sheet = Spreadsheet(filename)

        for row in sheet.get_row():
            booking_id = int(row[0])
            was_first_recurring = row[1] == "TRUE"

            res = db.query(Booking).filter(Booking.booking_id == booking_id).first()
            if res is None:
                print(f"{booking_id} was not found")
            elif res.was_first_recurring != was_first_recurring:
                print(
                    f"{booking_id = } {res.was_first_recurring = } => {was_first_recurring = }"
                )
                res.was_first_recurring = was_first_recurring
                if commit_flag:
                    print("db.session.commit()")
                    try:
                        db.commit()
                    except exc.SQLAlchemyError as e:
                        logger.error("Unable to update booking: %s", e)
                        db.rollback()
            else:
                print(f"{booking_id = } no change")
    finally:
        db.close()


if __name__ == "__main__":
    main()
