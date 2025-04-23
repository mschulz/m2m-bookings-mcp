from threading import Thread
from flask import current_app, render_template, request, has_request_context
from flask_mail import Message
from app import mail
import html2text
from email.mime.text import MIMEText
import base64
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build


def get_gmail_service():
    credentials = service_account.Credentials.from_service_account_info(
        json.loads(current_app.config['GMAIL_SERVICE_ACCOUNT_CREDENTIALS']),
        scopes=['https://www.googleapis.com/auth/gmail.send'],
        subject=current_app.config['FROM_ADDRESS']
    )
    service = build('gmail', 'v1', credentials=credentials)
    return service


# Converts a Flask-Mail Message to Gmail API format
def flask_message_to_gmail_raw(message: Message) -> dict:
    mime = MIMEText(message.body)
    mime['to'] = ', '.join(message.recipients)
    mime['subject'] = message.subject
    mime['from'] = message.sender or current_app.config['FROM_ADDRESS']

    raw = base64.urlsafe_b64encode(mime.as_bytes()).decode()
    return {'raw': raw}

def send_async_email(app, msg, subject, recipients):
    with app.app_context():
        try:
            service = get_gmail_service()
            raw_msg = flask_message_to_gmail_raw(msg)

            result = service.users().messages().send(userId='me', body=raw_msg).execute()
            
            current_app.logger.info(f'Email subject "{subject}" sent to {recipients}')
        except Exception as e:
            current_app.logger.error(f'Failed to send email to {recipients}\nReason: {e}')

def send_email(subject, sender, recipients, text_body, html_body):
    msg = Message(
            subject,
            sender=sender,
            recipients=recipients,
            body=text_body,
            html=html_body
    )
    Thread(target=send_async_email, args=(current_app._get_current_object(), msg, subject, recipients)).start()
     
def send_error_email(toaddr, error_msg):
    ''' Send developer email when an error has occurred. '''
    app_name = current_app.config["APP_NAME"]
    body = render_template('errors/error.html', app_name=app_name, error_msg=error_msg)
    where_str = f' in {request.path}' if has_request_context() else ''

    send_email(
        subject = f'{app_name}: Error has occurred{where_str}',
        sender=(current_app.config['FROM_NAME'], current_app.config["FROM_ADDRESS"]),
        recipients = toaddr if isinstance(toaddr, list) else [toaddr],
        html_body = body,
        text_body = html2text.html2text(body)
        )
     
def send_warning_email(toaddr, error_msg):
    ''' Send developer email when a warning has occurred. '''
    app_name = current_app.config["APP_NAME"]
    body = render_template('warning.html', app_name=app_name, error_msg=error_msg)
    where_str = f' in {request.path}' if has_request_context() else ''

    send_email(
        subject = f'{app_name}: Warning has occurred{where_str}',
        sender=(current_app.config['FROM_NAME'], current_app.config["FROM_ADDRESS"]),
        recipients = toaddr if isinstance(toaddr, list) else [toaddr],
        html_body = body,
        text_body = html2text.html2text(body)
        )
 
def send_success_email(toaddr, route):
    body = f"<h1>Success</h1><p>Route { route } successfully accessed.</p>"

    send_email(
        subject = f'{current_app.config["APP_NAME"]}: Success for {route}',
        sender=(current_app.config['FROM_NAME'], current_app.config["FROM_ADDRESS"]),
        recipients = toaddr if isinstance(toaddr, list) else [toaddr],
        html_body = body,
        text_body = html2text.html2text(body)
        )
     
def send_missing_location_email(toaddr, error_msg, locations, postcodes):
    ''' Send developer email when an error has occurred. '''
    company_name = current_app.config["COMPANY_NAME"]
    body = render_template(
                    'errors/missing_locations.html', 
                    app_name=company_name, 
                    error_msg=error_msg, 
                    number_locations=locations,
                    number_postcodes=postcodes
            )

    send_email(
        subject = f'{company_name}: Missing Location information!!',
        sender=(current_app.config['FROM_NAME'], current_app.config["FROM_ADDRESS"]),
        recipients = toaddr if isinstance(toaddr, list) else [toaddr],
        html_body = body,
        text_body = html2text.html2text(body)
        )
     

def send_updated_locations_email(toaddr, number_locations, updated, missing, postcodes):
    ''' Send developer email when an error has occurred. '''
    app_name = current_app.config["APP_NAME"]
    body = render_template(
                    'updated_bookings.html', 
                    app_name=app_name, 
                    number_locations=number_locations,
                    updated=updated,
                    missing=missing,
                    postcodes=postcodes
            )

    send_email(
        subject = f'{app_name}: Updated booking locations information!!',
        sender=(current_app.config['FROM_NAME'], current_app.config["FROM_ADDRESS"]),
        recipients = toaddr if isinstance(toaddr, list) else [toaddr],
        html_body = body,
        text_body = html2text.html2text(body)
        )

def send_completed_bookings_email(toaddr, bookings_count, n_active, tz_name):
    ''' Send support team an email detailing how many bookings were marked completed. '''
    app_name = current_app.config["APP_NAME"]
    body = render_template('completed.html', app_name=app_name, bookings_count=bookings_count, n_active=n_active, tz_name=tz_name)

    send_email(
        subject = f'{app_name}: {bookings_count} bookings marked completed',
        sender=(current_app.config['FROM_NAME'], current_app.config["FROM_ADDRESS"]),
        recipients = [toaddr],
        html_body = body,
        text_body = html2text.html2text(body)
        )


if __name__ == "__main__":
    from app import create_app
    
    app = create_app()
    
    with app.app_context():
        send_error_email('mark.f.schulz@gmail.com', 'Hope this is NOT an error for {current_app.config["APP_NAME"]}')
        # This should generate an error email from the logger
        send_error_email('mark.f.schulz', 'Hope this IS an err')
        