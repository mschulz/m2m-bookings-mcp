# app/logger.py

"""
    logger.py
        Provides a generic logging setup

        setup_logging is called during Flask initialization.  Must pass the 'app' object
        created by class Flask.
"""

import logging
from logging.handlers import SMTPHandler
import os


def setup_logging(app):
    '''
    setup_logging::
        log to logging files in directory $CWD/logs

    '''
    if app.config['LOG_TO_STDOUT'] or app.config['TESTING']:
        stream_handler = logging.StreamHandler()
        if not app.config['TESTING']:
            app.logger.setLevel(logging.INFO)
        else:
            app.logger.setLevel(logging.ERROR)
        app.logger.addHandler(stream_handler)

    if app.debug: return  # Do not send error emails while developing

        # Retrieve email settings from app.config
    host = app.config['MAIL_SERVER']
    port = 587  #app.config['MAIL_PORT']
    from_addr = app.config['FROM_ADDRESS']
    username = app.config['MAIL_USERNAME']
    password = app.config['MAIL_PASSWORD']
    secure = () if app.config.get('MAIL_USE_TLS') else None

    # Retrieve app settings from app.config
    m = app.config['SUPPORT_EMAIL'].split('@')
    to_addr_list = [ f"{m[0]}+error@{m[1]}" ]
    subject = app.config['APP_NAME'] + ': Error Detected'

    # Setup an SMTP mail handler for error-level messages
    mail_handler = SMTPHandler(
        mailhost=(host, port),  # Mail host and port
        fromaddr=from_addr,  # From address
        toaddrs=to_addr_list,  # To address
        subject=subject,  # Subject line
        credentials=(username, password),  # Credentials
        secure=(),
    )
    mail_handler.setLevel(logging.ERROR)
    app.logger.addHandler(mail_handler)

