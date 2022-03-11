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

from flask import jsonify
from app.report import report_api
from app.decorators import APIkey_required
from app.report.report import create_report


@report_api.route('/report', methods=['GET'])
@APIkey_required
def report():
    res = create_report()
    return jsonify(res)
