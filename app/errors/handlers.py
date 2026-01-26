from flask import request, current_app, jsonify
from app import db
from app.errors import bp
from app.email import send_error_email


@bp.app_errorhandler(401)
def unauthorized(error):
    report_issue("Method Not Unauthorized")
    return "Fail", 401


@bp.app_errorhandler(404)
def not_found_error(error):
    report_issue("Method Not Found")
    return "Fail", 404


@bp.app_errorhandler(422)
def unprocessable_entity(error):
    db.session.rollback()
    report_issue(error)
    return "Fail", 422


@bp.app_errorhandler(500)
def internal_error(e):
    db.session.rollback()
    report_issue(e)
    return "Fail", 500


@bp.app_errorhandler(503)
def temporary_error(e):
    db.session.rollback()
    report_issue(e)
    msg = {
        "status": "fail",
        "reason": "database is temporarily unavailable",
        "message": str(e),
    }
    return jsonify(msg), 503


def report_issue(e):
    m = current_app.config["SUPPORT_EMAIL"].split("@")
    to_addr = f"{m[0]}+error@{m[1]}"

    e_m = f"({request.path}) {str(e)}"
    current_app.logger.error(e_m)
    send_error_email(to_addr, e_m)
