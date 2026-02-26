"""Customer business logic for direct customer webhooks."""

import logging

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.daos.customer import customer_dao
from app.utils.klaviyo import notify_klaviyo

logger = logging.getLogger(__name__)


async def create_or_update_customer(data: dict, db: AsyncSession):
    """Validate and delegate customer upsert to the DAO."""
    if not data.get("id"):
        raise HTTPException(status_code=422, detail="Missing required field: id")
    await customer_dao.create_or_update_customer(db, data)
    return "OK"


async def create_new_customer(data: dict, service_category: str, db: AsyncSession):
    """Create a new Klaviyo profile and a new customer row in the database.

    Args:
        data: Customer dict with at least ``id``, ``email``, ``first_name``,
              ``phone``, and ``postcode``.
        service_category: "House Clean" or "Bond Clean" — determines which
              Klaviyo list the profile is added to.
        db: Async database session.
    """
    if not data.get("id"):
        raise HTTPException(status_code=422, detail="Missing required field: id")
    if not data.get("email"):
        raise HTTPException(status_code=422, detail="Missing required field: email")

    await notify_klaviyo(service_category, data)
    await customer_dao.create_or_update_customer(db, data)
    return "OK"
