from flask import request, render_template, current_app
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
    db.session.rollback()
    report_issue(e)
    return "Fail", 422    


@bp.app_errorhandler(500)
def internal_error(e):
    db.session.rollback()
    report_issue(e)
    return "Fail", 500    

def report_issue(e):
    m = current_app.config['SUPPORT_EMAIL'].split('@')
    to_addr = f"{m[0]}+error@{m[1]}"

    error_message = e.message
    if error_message:
        e_m = f'({request.path}) {error_message}'
    else:
        original = getattr(e, "original_exception", None)
        if original is None:
            e_m = f'({request.path}) Encountered an internal error in the server:\nReason: {e}'
        else:
            e_m = f'({request.path}) {original}'
    current_app.logger.error(e_m)
    send_error_email(to_addr, e_m)
    