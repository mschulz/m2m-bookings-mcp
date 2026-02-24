# app/daos/reservation.py

from app.daos.base import BaseDAO
from app.models.booking import Reservation


class ReservationDAO(BaseDAO):
    pass


reservation_dao = ReservationDAO(Reservation)
