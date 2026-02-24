# app/daos/sales_reservation.py

from app.daos.base import BaseDAO
from app.models.booking import SalesReservation


class SalesReservationDAO(BaseDAO):
    pass


sales_reservation_dao = SalesReservationDAO(SalesReservation)
