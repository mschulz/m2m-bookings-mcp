from threading import Thread
from flask import current_app
from flask_mail import Message
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
    mime = MIMEText(message.body, "html")
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


def send_email(subject, sender, recipients, html_body):
    msg = Message(
            subject,
            sender=sender,
            recipients=recipients,
            body=html_body
    )
    Thread(target=send_async_email, args=(current_app._get_current_object(), msg, subject, recipients)).start()

