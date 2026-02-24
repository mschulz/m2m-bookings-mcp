"""DAO for sales reservation records."""

from app.daos.base import BaseDAO
from app.models.booking import SalesReservation


class SalesReservationDAO(BaseDAO):
    """Data access for sales reservations; inherits all operations from BaseDAO."""


sales_reservation_dao = SalesReservationDAO(SalesReservation)
