# app/database/create_db.py

from .. import create_app
from app import db
from app.models import Booking, Customer


def main():
    ''' Create the initial database.  Should only call this once. '''


    app = create_app()

    with app.app_context():
        #db.drop_all()
        db.create_all()

if __name__ == '__main__':
    main()