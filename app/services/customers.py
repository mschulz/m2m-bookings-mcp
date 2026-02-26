"""Customer business logic for direct customer webhooks."""

import logging

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.daos.customer import customer_dao

logger = logging.getLogger(__name__)


def create_or_update_customer(data: dict, db: Session):
    """Validate and delegate customer upsert to the DAO."""
    if not data.get("id"):
        raise HTTPException(status_code=422, detail="Missing required field: id")
    customer_dao.create_or_update_customer(db, data)
    return "OK"
