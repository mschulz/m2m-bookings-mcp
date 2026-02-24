# app/daos/customer.py

import logging

from fastapi import HTTPException
from sqlalchemy import exc
from sqlalchemy.orm import Session

from app.models.customer import Customer

logger = logging.getLogger(__name__)


class CustomerDAO:
    def __init__(self, model):
        self.model = model

    def get_by_customer_id(self, db: Session, customer_id):
        return db.query(self.model).filter_by(customer_id=customer_id).first()

    def create_or_update_customer(self, db: Session, data):
        c = db.query(self.model).filter_by(customer_id=data["id"]).first()
        if c is None:
            c = Customer()
            c.import_customer(c, data)
            db.add(c)
            logger.info("Create row for new customer data")
        else:
            stored_update_time = c.updated_at
            c.import_customer(c, data)
            new_update_time = c.updated_at

            if stored_update_time == new_update_time:
                logger.info("No change to customer data")
                return
        try:
            db.commit()
            logger.info("Updated Customer data")
        except exc.DataError as e:
            db.rollback()
            raise HTTPException(
                status_code=422, detail=f"Customer error in model data: {e}"
            ) from e
        except exc.OperationalError:
            db.rollback()
            logger.info("SSL connection has been closed unexpectedly")


customer_dao = CustomerDAO(Customer)
