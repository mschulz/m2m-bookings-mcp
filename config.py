# config.py

import os
from dotenv import load_dotenv
import json

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))


class Config(object):
    API_KEY = os.environ.get('API_KEY')
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    
    # Company and app data - change with every app
    COMPANY_NAME = 'Template Company'
    COMPANY_URL = 'template.com.au'
    APP_NAME = 'Template'
    
    # Base level testing/debugging
    DEBUG = False
    TESTING = False
    CSRF_ENABLED = True
    
    # Timezone information
    TZ_LOCALTIME = os.environ.get('TZ_LOCALTIME', 'Australia/Brisbane')
    TZ_ISDST = os.environ.get('TZ_ISDST', None)
    
    # Database configuration
    DATABASE_TABLENAME = 'test_db'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', f'sqlite:///{basedir}/{DATABASE_TABLENAME}')
    #SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', "postgresql://localhost/{DATABASE_TABLENAME}")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Email settings
    FROM_NAME = os.environ.get('FROM_NAME')
    FROM_ADDRESS = os.environ.get('FROM_ADDRESS')
    #FROM_PASSWORD = os.environ.get('FROM_PASSWORD')
    SUPPORT_EMAIL = os.environ.get('SUPPORT_EMAIL')
    OVERRIDE_EMAIL = os.environ.get('OVERRIDE_EMAIL', 'True').lower() == 'true'

    # Used in web page configuration to allow update of phone numbers
    PHONE_NUMBER = os.environ.get('PHONE_NUMBER')
    
    # Flask-Mail settings
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 465
    MAIL_USE_TLS = False
    MAIL_USE_SSL = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', None)
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', None)
    MAIL_DEBUG = False
    
    # Custom fields
    CUSTOM_SOURCE = "drop_down:65c938ba-a125-48ba-a21f-9fb34350ab24"
    CUSTOM_BOOKED_BY = "single_line:a3a07fee-eb4f-42ae-ab31-9977d4d1acf9"
    CUSTOM_EMAIL_INVOICE = "drop_down:a255d2c7-fb9a-4fa8-beb6-a91bc1ef6fed"   

class ProductionConfig(Config):
    DEBUG = False  
    DEVELOPMENT = False
    LOG_TO_STDOUT = True
    TESTING = False  # This allows email sending :-(

class StagingConfig(Config):
    DEVELOPMENT = True
    DEBUG = True
    LOG_TO_STDOUT = True
    TESTING = False  # This allows email sending :-(

class DevelopmentConfig(Config):
    DEVELOPMENT = True
    DEBUG = False
    LOG_TO_STDOUT = True
    TESTING = False #True  # This suppresses email sending :-(

class TestingConfig(Config):
    TESTING = True  # This suppresses email sending :-(
    RATING_SERVER = "http://127.0.0.1:5000"
    LOG_TO_STDOUT = True
    