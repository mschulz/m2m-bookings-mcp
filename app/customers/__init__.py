# app/bookings/__init__.py

from flask import Blueprint

customers_api = Blueprint('customers', __name__)

from . import views