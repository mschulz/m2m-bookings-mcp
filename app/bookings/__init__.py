# app/bookings/__init__.py

from flask import Blueprint

bookings_api = Blueprint('booking', __name__)

from . import views