# app/bookings/__init__.py

from flask import Blueprint

report_api = Blueprint('report', __name__)

from . import views