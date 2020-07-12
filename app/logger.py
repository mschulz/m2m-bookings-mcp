# app/logger.py

"""
    logger.py
        Provides a generic logging setup

        setup_logging is called during Flask initialization.  Must pass the 'app' object
        created by class Flask.
"""

import logging
from logging.handlers import RotatingFileHandler
import os


def setup_logging(app):
    '''
    setup_logging::
        log to logging files in directory $CWD/logs

    '''
    if app.config['LOG_TO_STDOUT'] or app.config['TESTING']:
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(logging.INFO)
        app.logger.addHandler(stream_handler)
    else:            
        logs_path = os.path.join(os.getcwd(), "logs")
        if not os.path.exists(logs_path):
            os.mkdir(logs_path)
        file_handler = RotatingFileHandler('logs/ratings.log', maxBytes=10240,
                                           backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
        #file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

    if not app.config['TESTING']:
        app.logger.info('Logging to file initialized')
        app.logger.setLevel(logging.INFO)
    else:
        app.logger.setLevel(logging.ERROR)
        
