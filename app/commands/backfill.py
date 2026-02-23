# app/commands/backfill.py

"""
NOTE: This script depends on customer analytics DAO methods
(gain_cancelled_in_range, recurring_current, etc.) that were removed
during the FastAPI migration. It needs those methods restored to function.

A run-once program to calculate historical data and store in a table in the database.
    date, today gain, today loss, today nett, recurring count
"""

raise NotImplementedError(
    "backfill.py depends on removed customer analytics DAO methods. "
    "Restore gain_cancelled_in_range/recurring_current to BookingDAO if needed."
)
