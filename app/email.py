#app/email.py

from threading import Thread
from flask import current_app, render_template, has_request_context
from app.send_mail import send_email


def send_error_email(toaddr, error_msg):
    ''' Send developer email when an error has occurred. '''
    app_name = current_app.config["APP_NAME"]
    body = render_template('errors/error.html', app_name=app_name, error_msg=error_msg)
    where_str = f' in {request.path}' if has_request_context() else ''

    send_email(
        subject = f'{app_name}: Error has occurred{where_str}',
        sender=(current_app.config['FROM_NAME'], current_app.config["FROM_ADDRESS"]),
        recipients = toaddr if isinstance(toaddr, list) else [toaddr],
        html_body = body
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
        html_body = body
        )
 
def send_success_email(toaddr, route):
    body = f"<h1>Success</h1><p>Route { route } successfully accessed.</p>"

    send_email(
        subject = f'{current_app.config["APP_NAME"]}: Success for {route}',
        sender=(current_app.config['FROM_NAME'], current_app.config["FROM_ADDRESS"]),
        recipients = toaddr if isinstance(toaddr, list) else [toaddr],
        html_body = body
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
        html_body = body
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
        html_body = body
        )

def send_completed_bookings_email(toaddr, bookings_count, n_active, tz_name):
    ''' Send support team an email detailing how many bookings were marked completed. '''
    app_name = current_app.config["APP_NAME"]
    body = render_template('completed.html', app_name=app_name, bookings_count=bookings_count, n_active=n_active, tz_name=tz_name)

    send_email(
        subject = f'{app_name}: {bookings_count} bookings marked completed',
        sender=(current_app.config['FROM_NAME'], current_app.config["FROM_ADDRESS"]),
        recipients = [toaddr],
        html_body = body
        )


if __name__ == "__main__":
    from app import create_app
    
    app = create_app()
    
    with app.app_context():
        send_error_email('mark.f.schulz@gmail.com', f'Hope this is NOT an error for {current_app.config["APP_NAME"]}')
        # This should generate an error email from the logger
        send_error_email('mark.f.schulz', 'Hope this IS an err')
        