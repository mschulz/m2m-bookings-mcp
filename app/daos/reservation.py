"""DAO for NDIS reservation records."""

from app.daos.base import BaseDAO
from app.models.booking import Reservation


class ReservationDAO(BaseDAO):
    """Data access for NDIS reservations; inherits all operations from BaseDAO."""


reservation_dao = ReservationDAO(Reservation)
