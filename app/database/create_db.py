# app/database/create_db.py

from .. import create_app
from app import db


def main():
    """Create the initial database.  Should only call this once."""
    app = create_app()
    with app.app_context():
        # db.drop_all()
        db.create_all()
        db.session.commit()


if __name__ == "__main__":
    main()
