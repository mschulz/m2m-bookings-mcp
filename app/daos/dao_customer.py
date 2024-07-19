# app/daos/dao_sales_reservation.py

from datetime import datetime, timedelta
import pytz
import pendulum as pdl

from app import db

from app.models.model_customer import Customer
from flask import current_app, abort, request
from sqlalchemy import exc


class CustomerDAO:
    def __init__(self, model):
        self.model = model

    def get_by_customer_id(self, customer_id):
        return db.session.query(self.model).filter_by(customer_id = customer_id).first()

    def create_or_update_customer(self, data):
        # Update the customer information table, if it has been updated since the last time it was stored
        #current_app.logger.info(f'Customer data received: {data}')

        c = db.session.query(self.model).filter_by(customer_id = data['id']).first()
        if c is None:
            # Nothing stored about this customer, so create a new row in the table
            c = Customer()
            c.import_customer(c, data)
            db.session.add(c)
            current_app.logger.info(f'Create row for new customer data')
        else:
            # Check if there is updated data in the customer fields
            # First get the updated_at time from the stored data
            stored_update_time = c.updated_at
            c.import_customer(c, data)
            new_update_time = c.updated_at
        
            # Check if the data has been updated since the last time it was stored in the table
            if stored_update_time == new_update_time:
                current_app.logger.info(f'No change to customer data')
                return
        try:
            db.session.commit()
            current_app.logger.info(f'({request.path}) Updated Customer data')
        except exc.DataError as e:
            db.session.rollback()
            abort(422, description=f'Customer error in model data: {e}')
        except exc.OperationalError as e:
            db.session.rollback()
            current_app.logger.info(f'SSL connection has been closed unexpectedly')

customer_dao = CustomerDAO(Customer)


