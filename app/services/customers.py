"""Customer business logic for direct customer webhooks."""

import logging

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.daos.customer import customer_dao

logger = logging.getLogger(__name__)


async def create_or_update_customer(data: dict, db: AsyncSession):
    """Validate and delegate customer upsert to the DAO."""
    if not data.get("id"):
        raise HTTPException(status_code=422, detail="Missing required field: id")
    await customer_dao.create_or_update_customer(db, data)
    return "OK"
