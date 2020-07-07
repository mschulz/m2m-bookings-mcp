from flask import render_template, current_app
from app import db
from app.errors import bp
from app.email import send_error_email

@bp.app_errorhandler(401)
def unauthorized(error):
    return render_template('errors/401.html'), 401


@bp.app_errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@bp.app_errorhandler(422)
def unprocessable_entity(error):
    return render_template('errors/422.html'), 422


@bp.app_errorhandler(500)
def internal_error(e):
    db.session.rollback()
    
    original = getattr(e, "original_exception", None)
    if original is None:
        # direct 500 error, such as abort(500)
        error_msg = f'Encountered an internal error in the server:\nReason: {e}'
        send_error_email(current_app.config['SUPPORT_EMAIL'], error_msg)
    else:
        send_error_email(current_app.config['SUPPORT_EMAIL'], original)
    return render_template("errors/500.html"), 500    
