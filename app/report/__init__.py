# app/report/__init__.py

from flask import Blueprint

report_api = Blueprint("reports", __name__)

from . import views
