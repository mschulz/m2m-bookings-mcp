from threading import Thread
from flask import current_app, render_template, request, has_request_context
from flask_mail import Message
from app import mail
import html2text
import smtplib


def send_async_email(app, msg, subject, recipients):
    with app.app_context():
        try:
            mail.send(msg)
            current_app.logger.info(f'Email subject "{subject}" sent to {recipients}')
        except smtplib.SMTPAuthenticationError as e:
            current_app.logger.error(f'Failed to send email to {recipients}\nReason: {e}')

def send_email(subject, sender, recipients, text_body, html_body):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
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

if __name__ == '__main__':

    import os
    from flask import Flask

    #from urllib.parse import urlparse
    from flask_mail import Mail
    from app.logger import setup_logging

    mail = Mail()

    app = Flask(__name__, instance_relative_config=True, static_url_path='')
    app.config.from_object(os.environ['APP_SETTINGS'])

    #initialise the logger
    setup_logging(app)

    # Set up mail
    mail.init_app(app)

    # This is meant to FAIL, and so force an email rep[orting the error
    with app.app_context():
        send_success_email("mark.f.schulz@gmail.com")