# app/customers/views.py

import json
import datetime

from flask import request, current_app, abort, jsonify
from app import db
from app.customers import customers_api
from app.decorators import APIkey_required
from app.daos import booking_dao


@customers_api.route('/customers/gain', methods=['GET'])
@APIkey_required
def gain():
    ''' 
        return number of new recurring customers gained over the period
    '''
    start_date_str = request.args.get('end_date', type=str)
    month = request.args.get('month', type=int)
    if start_date_str:
        period_days = request.args.get('period', type=int)
        gain = booking_dao.get_gain(start_date_str, period_days, prior=True)
        result = {
            "status" :"success",
            "gain": gain
        }
        return jsonify(result), 200
    elif month:
        if isinstance(month, str):
            month = int(month)
        date = datetime.date.today()
        current_year = date.strftime("%Y")
        year = request.args.get('year', default=current_year, type=int)
        if isinstance(year, str):
            year = int(year)
        gain = booking_dao.get_gain_by_month(month, year)
        result = {
            "status" :"success",
            "gain": gain
        }
        return jsonify(result), 200
    else:
        # Return invalid parameters message
        result = {
            "status" :"fail",
            "message": "Invalid/missing parameters"
        }
        return jsonify(result), 400


@customers_api.route('/customers/loss', methods=['GET'])
@APIkey_required
def loss():
    ''' 
        return number of new recurring customers gained over the period
    '''
    start_date_str = request.args.get('end_date', type=str)
    month = request.args.get('month', type=int)
    if start_date_str:
        period_days = request.args.get('period', type=int)
        loss = booking_dao.get_loss(start_date_str, period_days, prior=True)
        result = {
            "status" :"success",
            "loss": loss
        }
        return jsonify(result), 200
    elif month:
        if isinstance(month, str):
            month = int(month)
        date = datetime.date.today()
        current_year = date.strftime("%Y")
        year = request.args.get('year', default=current_year, type=int)
        if isinstance(year, str):
            year = int(year)
        loss = booking_dao.get_loss_by_month(month, year)
        result = {
            "status" :"success",
            "loss": loss
        }
        return jsonify(result), 200
    else:
        # Return invalid parameters message
        result = {
            "status" :"fail",
            "message": "Invalid/missing parameters"
        }
        return jsonify(result), 400


@customers_api.route('/customers/nett', methods=['GET'])
@APIkey_required
def nett():
    ''' 
        return number of new recurring customers gained over the period
    '''
    start_date_str = request.args.get('end_date', type=str)
    month = request.args.get('month', type=int)
    if start_date_str:
        period_days = request.args.get('period', type=int)
        gain = booking_dao.get_gain(start_date_str, period_days, prior=True)
        loss = booking_dao.get_loss(start_date_str, period_days, prior=True)
        result = {
            "nett": gain - loss
        }
        return jsonify(result), 200
    elif month:
        if isinstance(month, str):
            month = int(month)
        date = datetime.date.today()
        current_year = date.strftime("%Y")
        year = request.args.get('year', default=current_year, type=int)
        if isinstance(year, str):
            year = int(year)
        gain = booking_dao.get_gain_by_month(month, year)
        loss = booking_dao.get_loss_by_month(month, year)
        result = {
            "nett": gain - loss
        }
        return jsonify(result), 200
    else:
        # Return invalid parameters message
        result = {
            "status" :"fail",
            "message": "Invalid/missing parameters"
        }
        return jsonify(result), 400


"""def local_to_UTC(d):
    local = pytz.timezone(current_app.config['TZ_LOCALTIME'])
    local_dt = local.localize(d, is_dst=current_app.config['TZ_ISDST'])
    utc_dt = local_dt.astimezone(pytz.utc)
    return utc_dt"""