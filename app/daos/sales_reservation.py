# app/daos/sales_reservation.py

from app.daos.base import BaseDAO
from app.models.booking import SalesReservation


class SalesReservationDAO(BaseDAO):
    def __init__(self, model):
        super().__init__(model)


sales_reservation_dao = SalesReservationDAO(SalesReservation)
