# app/logger.py

"""
logger.py
    Provides a customized logging setup for STDOUT, Insight logging service, and Posting emails for errors.
"""

import logging
from app.gmail_handler import GmailOAuth2Handler


def setup_logging(app):
    """
    setup_logging::
        setup_logging is called during Flask initialization.  Must pass the 'app' object
        created by class Flask.

    """
    if app.config["LOG_TO_STDOUT"] or app.config["TESTING"]:
        stream_handler = logging.StreamHandler()
        if not app.config["TESTING"]:
            app.logger.setLevel(logging.INFO)
        else:
            app.logger.setLevel(logging.ERROR)
        app.logger.addHandler(stream_handler)

    if app.debug:
        return  # Do not send error emails while developing

    # Retrieve app settings from app.config
    m = app.config["SUPPORT_EMAIL"].split("@")
    to_addr = f"{m[0]}+error@{m[1]}"
    subject = app.config["APP_NAME"] + ": Error Detected"

    # Setup an GMAIL mail handler for error-level messages
    mail_handler = GmailOAuth2Handler(app, to_addr, subject)
    mail_handler.setLevel(logging.ERROR)
    app.logger.addHandler(mail_handler)
