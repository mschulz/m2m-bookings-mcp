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
    COMPANY_NAME = os.environ.get('COMPANY_NAME')
    COMPANY_URL = os.environ.get('COMPANY_URL')
    APP_NAME = os.environ.get('APP_NAME')
    PHONE = os.environ.get('PHONE')
    
    RATING_SERVER = os.environ.get('RATING_SERVER')
    
    # Base level testing/debugging
    DEBUG = False
    TESTING = False
    CSRF_ENABLED = True
    
    # Timezone information
    TZ_LOCALTIME = os.environ.get('TZ_LOCALTIME', 'Australia/Brisbane')
    TZ_ISDST = os.environ.get('TZ_ISDST', None)
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'postgres:///test').replace('postgres://', 'postgresql://')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_ENGINE_OPTIONS = { 'pool_pre_ping': True }
    
    # accessing our Launch27 proxy
    L27_URL = os.environ.get('L27_URL')
    L27_API_KEY = os.environ.get('L27_API_KEY')
    
    # Email settings
    FROM_NAME = os.environ.get('FROM_NAME')
    FROM_ADDRESS = os.environ.get('FROM_ADDRESS')
    SUPPORT_EMAIL = os.environ.get('SUPPORT_EMAIL')
    OVERRIDE_EMAIL = os.environ.get('OVERRIDE_EMAIL', 'True').lower() == 'true'
    OVERRIDE_ADDR = os.environ.get('OVERRIDE_ADDR')
    

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
    MISSING_LOCATION_EMAIL=os.environ.get('MISSING_LOCATION_EMAIL')
    
    # SendinBlue configuration
    SMTP_KEY = 'REDACTED_SMTP_KEY'
    SMTP_SERVER = 'smtp-relay.sendinblue.com'
    SMTP_LOGIN = 'mark.f.schulz@gmail.com'
    SMTP_PORT = 587
    SIB_API_KEY = 'REDACTED_SIB_KEY'
    PLUGINS_KEY = 'REDACTED_SMTP_KEY'
    
    # Launch27 details for bookings
    L27_USERNAME = os.environ.get('L27_USERNAME')
    L27_PASSWORD = os.environ.get('L27_PASSWORD')
    
    # Custom fields
    CUSTOM_SOURCE = os.environ.get('CUSTOM_SOURCE')
    CUSTOM_BOOKED_BY = os.environ.get('CUSTOM_BOOKED_BY')
    CUSTOM_EMAIL_INVOICE = os.environ.get('CUSTOM_EMAIL_INVOICE')
    CUSTOM_INVOICE_NAME = os.environ.get('CUSTOM_INVOICE_NAME')
    CUSTOM_WHO_PAYS = os.environ.get('CUSTOM_WHO_PAYS')
    CUSTOM_INVOICE_EMAIL_ADDRESS = os.environ.get('CUSTOM_INVOICE_EMAIL_ADDRESS')
    CUSTOM_LAST_SERVICE = os.environ.get('CUSTOM_LAST_SERVICE', None)
    CUSTOM_INVOICE_REFERENCE = os.environ.get('CUSTOM_INVOICE_REFERENCE', None)
    CUSTOM_INVOICE_REFERENCE_EXTRA = os.environ.get('CUSTOM_INVOICE_REFERENCE_EXTRA', None)
    CUSTOM_NDIS_NUMBER = os.environ.get('CUSTOM_NDIS_NUMBER', None)
    CUSTOM_FLEXIBLE = os.environ.get('CUSTOM_FLEXIBLE', None)
    CUSTOM_HOURLY_NOTES = os.environ.get('CUSTOM_HOURLY_NOTES', None)
    
    # SendInBlue details
    SENDINBLUE_API_KEY = os.environ.get('SENDINBLUE_API_KEY')
    SENDINBLUE_URL = os.environ.get('SENDINBLUE_URL')
    SENDINBLUE_FROM_NAME = os.environ.get('SENDINBLUE_FROM_NAME')
    SENDINBLUE_FROM_EMAIL = os.environ.get('SENDINBLUE_FROM_EMAIL')
    TEMPLATE_ID_CONFIRMATION = int(os.environ.get('TEMPLATE_ID_CONFIRMATION'))
    TEMPLATE_ID_FIRST_HEADSUP = int(os.environ.get('TEMPLATE_ID_FIRST_HEADSUP'))
    TEMPLATE_ID_SECOND_HEADSUP = int(os.environ.get('TEMPLATE_ID_SECOND_HEADSUP'))
    TEMPLATE_ID_RATING = int(os.environ.get('TEMPLATE_ID_RATING'))
    
    # service_category default for each business
    SERVICE_CATEGORY_DEFAULT = os.environ.get('SERVICE_CATEGORY_DEFAULT')
    RESERVATION_CATEGORY = os.environ.get('RESERVATION_CATEGORY', 'NDIS Reservation')
    SALES_RESERVATION_CATEGORY = os.environ.get('SALES_RESERVATION_CATEGORY', 'Sales Reservation')
    
    # Klaviyo updates
    MY_KLAVIYO_URL = os.environ.get('MY_KLAVIYO_URL')
    MY_KLAVIYO_API_KEY = os.environ.get('MY_KLAVIYO_API_KEY')
     
    # Notification webhook
    NOTIFICATION_URL = os.environ.get('NOTIFICATION_URL')
    
    # zip2location URL
    ZIP2LOCATION_URL = os.environ.get('ZIP2LOCATION_URL')
    
    # new-bond-agent-calls Zapier URL
    NEW_BOND_AGENT_CALLS = os.environ.get('NEW_BOND_AGENT_CALLS', None)

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
    DEBUG = True
    