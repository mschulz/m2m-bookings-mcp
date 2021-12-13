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
from app.customers import customers_api
from app.decorators import APIkey_required
from app.reports import create_report

@customers_api.route('/report', methods=['GET'])
@APIkey_required
def report():
    res = create_report()
    return jsonify(res)

