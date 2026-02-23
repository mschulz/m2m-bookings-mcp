# app/daos/reservation.py

from app.daos.base import BaseDAO
from app.models.booking import Reservation


class ReservationDAO(BaseDAO):
    def __init__(self, model):
        super().__init__(model)


reservation_dao = ReservationDAO(Reservation)
