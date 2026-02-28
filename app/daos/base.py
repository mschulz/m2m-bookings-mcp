"""Base DAO with shared CRUD operations for all booking types."""

import logging

from fastapi import HTTPException
from sqlalchemy import exc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.utils.locations import get_location
from app.utils.validation import truncate_field, safe_int

logger = logging.getLogger(__name__)


async def _resolve_location(instance, data: dict, id_field: str = "id"):
    """Look up location from postcode if not provided in webhook data."""
    if instance.postcode and not data.get("location"):
        bid = data.get(id_field)
        location = await get_location(instance.postcode)
        if location:
            instance.location = truncate_field(location, 64, "location", bid)


async def safe_commit(
    db: AsyncSession,
    error_detail: str,
    integrity_msg: str | None = None,
) -> bool:
    """Commit with standardised error handling. Returns True on success.

    - DataError → rollback + raise HTTPException(422)
    - IntegrityError → rollback + log integrity_msg (if provided; otherwise re-raises)
    - OperationalError → rollback + log
    """
    try:
        await db.commit()
        return True
    except exc.DataError as e:
        await db.rollback()
        raise HTTPException(
            status_code=422, detail=f"Data error: {error_detail}"
        ) from e
    except exc.IntegrityError:
        await db.rollback()
        if integrity_msg:
            logger.info(integrity_msg)
        else:
            raise
    except exc.OperationalError:
        await db.rollback()
        logger.info("SSL connection has been closed unexpectedly")
    return False


class BaseDAO:
    def __init__(self, model):
        self.model = model

    async def get_by_booking_id(self, db: AsyncSession, booking_id):
        """Look up a single record by its external booking_id."""
        result = await db.execute(
            select(self.model).where(self.model.booking_id == booking_id)
        )
        return result.scalars().first()

    async def create_update_booking(self, db: AsyncSession, new_data):
        """Upsert a booking record: insert if new, update if existing."""
        booking_id = safe_int(new_data.get("id"))
        if not booking_id:
            logger.error("booking has no booking_id - ignore this data")
            raise HTTPException(status_code=422, detail="booking has no booking_id")

        result = await db.execute(
            select(self.model).where(self.model.booking_id == booking_id)
        )
        b = result.scalars().first()

        if b is None:
            logger.info("haven't seen this booking - ADDING to database")
            b = self.model.from_webhook(new_data)
            await _resolve_location(b, new_data)
            db.add(b)
        else:
            logger.info("have seen this booking - UPDATING database")
            b.update_from_webhook(new_data)
            await _resolve_location(b, new_data)
            logger.info(
                'Loading ... Name: "%s" team: "%s" booking_id: %s',
                b.name, b.teams_assigned, b.booking_id,
            )

        await safe_commit(
            db, str(b.model_dump()),
            f"Data already loaded into database: {b.model_dump()}",
        )

    async def update_booking(self, db: AsyncSession, new_data):
        """Apply cancellation-specific updates to an existing booking."""
        booking_id = safe_int(new_data.get("booking_id"))
        result = await db.execute(
            select(self.model).where(self.model.booking_id == booking_id)
        )
        b = result.scalars().first()
        logger.info("have seen this booking - UPDATING database")

        b.update_from_cancellation(new_data)
        await _resolve_location(b, new_data, id_field="booking_id")

        logger.info(
            'Loading ... Name: "%s" team: "%s" booking_id: %s',
            b.name, b.teams_assigned, b.booking_id,
        )

        await safe_commit(
            db, str(b.model_dump()),
            f"Data already loaded into database: {b.model_dump()}",
        )

    async def cancel_booking(self, db: AsyncSession, new_data):
        """Delete a booking record by its external booking_id."""
        booking_id = safe_int(new_data.get("id"))
        if booking_id is None:
            return
        result = await db.execute(
            select(self.model).where(self.model.booking_id == booking_id)
        )
        row = result.scalars().first()
        if row:
            await db.delete(row)
        if await safe_commit(db, str(new_data), f"Integrity error: {new_data}"):
            logger.info("Booking deleted from table: %s", booking_id)
