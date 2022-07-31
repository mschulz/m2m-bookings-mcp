# /app/__init__.py
'''
__init__.py

This module sets up the environment for Flask to run under, initialising all
the services used.
'''

import os
from flask import Flask

#from urllib.parse import urlparse
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from app.logger import setup_logging
from app.local_date_time import get_local_date_time_now

# Set up the database
db = SQLAlchemy()
mail = Mail()

def create_app():
    '''
    create_app::
        Initialise  everything
        1. Load the configuration information
        2. set up the local time
        3. set up logging to files in /app/logs/
        4. set up SMTP mail using Flask-Mail
        5. Initialise the PostGres database
        6. Load up the Blueprints (which load the views)
    '''
    global local_date, local_time

    app = Flask(__name__, instance_relative_config=True, static_url_path='')
    app.config.from_object(os.environ['APP_SETTINGS'])

    #ovrrd = app.config["OVERRIDE_EMAIL"]
    if not app.config['TESTING']:
        print(f'OVERRIDE_EMAIL: {app.config["OVERRIDE_EMAIL"]}')
    # Determine date and time where based - servers are mostlikely in the US
    #local_date, local_time = get_local_date_time_now(app.config['TZ_LOCALTIME'], app.config['TZ_ISDST'])

    #initialise the logger
    setup_logging(app)
    if not app.config['TESTING']:
        app.logger.info(f'{app.config["APP_NAME"]}: starting ...')
        app.logger.info(f'database: {app.config["SQLALCHEMY_DATABASE_URI"]}')

    # Set up mail
    mail.init_app(app)

    # Set up the SQL database
    db.init_app(app)

    # Load up the data for mapping locations to Google Review URLs.
    #   If the spreadsheet changes we need to restart this program.
    # gr = GoogleReview(config.db_idx_url_filename, config.db_idx_loc_filename,
    # config.db_pc_idx_filename)

    # Register the blueprints
    register_blueprints(app)

    return app


def register_blueprints(app):
    from app.errors import bp as errors_bp
    app.register_blueprint(errors_bp)
    
    from app.bookings import bookings_api as bookings_api_blueprint
    app.register_blueprint(bookings_api_blueprint)
    from app.customers import customers_api as customers_api_blueprint
    app.register_blueprint(customers_api_blueprint)
    from app.report import report_api as report_api_blueprint
    app.register_blueprint(report_api_blueprint)
    
