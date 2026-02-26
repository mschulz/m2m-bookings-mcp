"""Customer webhook endpoints."""

import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import verify_api_key
from app.core.database import get_db
from app.services.customers import create_or_update_customer

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/customer",
    tags=["customers"],
    dependencies=[Depends(verify_api_key)],
)


@router.post("/new", operation_id="create_new_customer")
def new(data: dict, db: Session = Depends(get_db)):
    """Receive a new customer webhook from Zapier. Creates or updates the customer record."""
    logger.info("Processing a new customer ...")
    return create_or_update_customer(data, db)


@router.post("/updated", operation_id="update_customer")
def updated(data: dict, db: Session = Depends(get_db)):
    """Receive an updated customer webhook from Zapier. Updates existing customer data."""
    logger.info("Processing an updated customer ...")
    return create_or_update_customer(data, db)
