"""Customer DAO for creating and updating customer records."""

import logging

from fastapi import HTTPException
from sqlalchemy import exc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.daos.base import _resolve_location
from app.models.customer import Customer
from app.utils.validation import safe_int

logger = logging.getLogger(__name__)


class CustomerDAO:
    def __init__(self, model):
        self.model = model

    async def get_by_customer_id(self, db: AsyncSession, customer_id):
        """Look up a customer by their external customer_id."""
        result = await db.execute(
            select(self.model).where(self.model.customer_id == customer_id)
        )
        return result.scalars().first()

    async def create_or_update_customer(self, db: AsyncSession, data):
        """Upsert a customer record, skipping commit if data is unchanged."""
        result = await db.execute(
            select(self.model).where(self.model.customer_id == safe_int(data["id"]))
        )
        c = result.scalars().first()
        if c is None:
            c = Customer.from_webhook(data)
            await _resolve_location(c, data)
            db.add(c)
            logger.info("Create row for new customer data")
        else:
            stored_update_time = c.updated_at
            c.update_from_webhook(data)
            await _resolve_location(c, data)
            new_update_time = c.updated_at

            if stored_update_time == new_update_time:
                logger.info("No change to customer data")
                return
        try:
            await db.commit()
            logger.info("Updated Customer data")
        except exc.DataError as e:
            await db.rollback()
            raise HTTPException(
                status_code=422, detail=f"Customer error in model data: {e}"
            ) from e
        except exc.OperationalError:
            await db.rollback()
            logger.info("SSL connection has been closed unexpectedly")


customer_dao = CustomerDAO(Customer)
