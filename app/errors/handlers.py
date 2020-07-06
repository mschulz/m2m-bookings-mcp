from flask import render_template, current_app
from app import db
from app.errors import bp
from app.email import send_error_email

@bp.app_errorhandler(401)
def not_found_error(error):
    return render_template('errors/401.html'), 401


@bp.app_errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@bp.app_errorhandler(500)
def internal_error(error):
    db.session.rollback()
    error_msg = 'Encountered an internal error in the server'
    send_error_email(current_app.config['SUPPORT_EMAIL'], error_msg)
    return render_template('errors/500.html'), 500
