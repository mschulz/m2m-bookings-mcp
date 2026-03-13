"""
Command script: report bookings with missing location data.

Queries all bookings whose ``location`` field is NULL, deduplicates the
affected postcodes, and emails a summary to the support address.

Usage::

    python -m app.database.missing_locations

The script is safe to run in any environment.  In ``testing`` mode the email
is suppressed by the email service layer, but the DB query and logging still
execute normally.
"""

import asyncio
import logging

from app.core.config import get_settings
from app.core.database import async_session
from app.core.logging_config import setup_logging
from app.daos.booking import booking_dao
from app.utils.email_service import send_missing_location_email

logger = logging.getLogger(__name__)


async def find_missing_locations() -> dict:
    """Query the database and return a summary of bookings with no location.

    Returns a dict with:

    * ``total``      – total number of bookings missing a location
    * ``postcodes``  – sorted list of unique postcodes involved (NULLs excluded)

    The function opens its own ``AsyncSession`` so it can be called from a
    standalone script or scheduled job without a live HTTP request context.
    """
    async with async_session() as db:
        bookings = await booking_dao.get_bookings_missing_locations(db)

    total = len(bookings)
    logger.info("Bookings missing location: %d", total)

    # Deduplicate postcodes; skip rows where postcode itself is also NULL.
    postcodes = sorted({b.postcode for b in bookings if b.postcode is not None})
    logger.info("Distinct postcodes affected: %d → %s", len(postcodes), postcodes)

    return {"total": total, "postcodes": postcodes}


async def main() -> None:
    """Entry point: find missing-location bookings and send the alert email."""
    setup_logging()
    settings = get_settings()
    logger.info("%s: missing_locations script starting", settings.APP_NAME)

    summary = await find_missing_locations()

    total = summary["total"]
    postcodes = summary["postcodes"]
    n_postcodes = len(postcodes)

    if total == 0:
        logger.info("No bookings with missing locations — nothing to report.")
        return

    logger.info(
        "Sending missing-location alert: %d bookings, %d postcodes",
        total,
        n_postcodes,
    )

    toaddr = settings.SUPPORT_EMAIL
    msg = str(postcodes)

    # email_service is synchronous (Google API); run in a thread to avoid
    # blocking the event loop.
    await asyncio.to_thread(
        send_missing_location_email, toaddr, msg, total, n_postcodes
    )

    logger.info(
        "%s: missing_locations script complete — alert sent to %s",
        settings.APP_NAME,
        toaddr,
    )


if __name__ == "__main__":
    asyncio.run(main())
