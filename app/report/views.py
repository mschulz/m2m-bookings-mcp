# app/report/views.py

"""
Return customer summary data:
    for all - Net, Gain, Loss
        Today
        Yesterday
        This Week (to date)
        This Month (to date)

    Recurring customer count
"""

from sqlalchemy import exc
from flask import jsonify

from app.report import report_api
from app.decorators import APIkey_required
from app.report.report import create_report


@report_api.route("/report", methods=["GET"])
@APIkey_required
def report():
    try:
        res = create_report()
        return jsonify(res)
    except exc.OperationalError as e:
        msg = {
            "status": "fail",
            "reason": "database is temporarily unavailable",
            "message": e,
        }
        return jsonify(msg), 503
