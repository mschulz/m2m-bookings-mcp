# app/daos.py

"""
    Contains all the Data Access Objects (DAOs)

    Services/DAO Singleton Design Pattern: A pattern I have found that works very well in a Flask app is the services/dao (database access object) singleton pattern. The summary of this pattern is outlined below:
        Business logic is placed in services methods.
        Database access (ORM) is in dao methods which use models.
        Routes are kept light and either use service or dao methods.

"""
from app import db
from sqlalchemy import exc
from flask import current_app, abort


class BaseDAO:
    def __init__(self, model):
        self.model = model

    def get_by_booking_id(self, booking_id):
        return db.session.query(self.model).filter_by(booking_id = booking_id).first()
    
    def create_update_booking(self, new_data):
        booking_id = new_data['id'] if 'id' in new_data else None
        if not booking_id:
            # This is a malformed set of data (this test might be redundant)
            current_app.logger.error("booking has no booking_id - ignore this data")
            abort(422, description="booking has no booking_id - ignore this data")
        
        # Check if we already have a booking under this id
        b = db.session.query(self.model).filter_by(booking_id = booking_id).first()
    
        if b is None:
            # Haven't seen the original booking - ADD it now
            current_app.logger.info("haven't seen this booking - ADDING to database")
    
            # Load the database table
            b = self.model()
            b.import_dict(b, new_data)
            db.session.add(b)
        else:
            # Have seen the original booking - UPDATE it now
            current_app.logger.info("have seen this booking - UPDATING database")
    
            bb = self.model()
            bb.import_dict(b, new_data)
    
            current_app.logger.info(f'Loading ... Name: "{b.name}" team: "{b.teams_assigned}" booking_id: {b.booking_id}')
    
        try:
            db.session.commit()
            #current_app.logger.info(f'Data loaded into database: {b.to_dict()}')
        except exc.DataError as e:
            abort(422, description=f'Data loaded into database: {b.to_dict()}')
        except exc.IntegrityError as e:
            db.session.rollback()
            current_app.logger.info(f'Data already loaded into database: {b.to_dict()}')
        except exc.OperationalError as e:
            db.session.rollback()
            current_app.logger.info(f'SSL connection has been closed unexpectedly')

    def update_booking(self, new_data):
        booking_id = new_data['booking_id'] if 'booking_id' in new_data else None
        b = db.session.query(self.model).filter_by(booking_id = booking_id).first()
        current_app.logger.info("have seen this booking - UPDATING database")

        import_cancel_dict(b, new_data)

        current_app.logger.info(f'Loading ... Name: "{b.name}" team: "{b.teams_assigned}" booking_id: {b.booking_id}')

        try:
            db.session.commit()
            #current_app.logger.info(f'Data loaded into database: {b.to_dict()}')
        except exc.DataError as e:
            abort(422, description=f'Data loaded into database: {b.to_dict()}')
        except exc.IntegrityError as e:
            db.session.rollback()
            current_app.logger.info(f'Data already loaded into database: {b.to_dict()}')
        except exc.OperationalError as e:
            db.session.rollback()
            current_app.logger.info(f'SSL connection has been closed unexpectedly')


    def cancel_booking(self, new_data):
        booking_id = new_data['id'] if 'id' in new_data else None
        if booking_id is None:
            return
        b = db.session.query(self.model).filter_by(booking_id = booking_id).delete()
        try:
            db.session.commit()
            current_app.logger.info(f'NDIS Reservation deleted from table: {booking_id}')
        except exc.DataError as e:
            abort(422, description=f'Reservation data error: {new_data}')
        except exc.IntegrityError as e:
            db.session.rollback()
            current_app.logger.info(f'NDIS Reservation Inegrity error: {new_data}')
        except exc.OperationalError as e:
            db.session.rollback()
            current_app.logger.info(f'SSL connection has been closed unexpectedly')

