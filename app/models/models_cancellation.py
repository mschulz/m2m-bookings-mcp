# app/models/model_cancel.py

from flask import current_app
from app.models_base import check_postcode 
from app.locations import get_location


def import_cancel_dict(d, b):
    d.booking_id = b['booking_id']
    d.updated_at = b.get('updated_at')
    d.cancellation_type = b.get('cancellation_type')
    d.cancelled_by = b.get('cancelled_by')
    d.cancellation_date = b.get('cancellation_date')
    d._cancellation_datetime = b.get('_cancellation_datetime')
    d.cancellation_reason = b.get('cancellation_reason')
    d.cancellation_fee = b.get('cancellation_fee')
    d.booking_status = b.get('booking_status')
    d.is_first_recurring = b.get('is_first_recurring')
    if d.is_first_recurring:
        d.was_first_recurring = True
    d.is_new_customer = b.get('is_new_customer')
    if d.is_new_customer:
        d.was_new_customer = True
    d.postcode = check_postcode(b, "booking_id", b['booking_id'])
    if d.postcode:
        d.location = b.get('location'], get_location(d.postcode))
    
    # Custom field data
    if 'custom_fields' in b:
        b_cf = b["custom_fields"]
        
        ## How did you find Maid2Match
        CUSTOM_SOURCE = current_app.config['CUSTOM_SOURCE']
        if CUSTOM_SOURCE and CUSTOM_SOURCE in b_cf:
            d.lead_source = b_cf[CUSTOM_SOURCE][:64]
        
        # Which team member booked this clean in?
        CUSTOM_BOOKED_BY = current_app.config['CUSTOM_BOOKED_BY']
        if CUSTOM_BOOKED_BY and CUSTOM_BOOKED_BY in b_cf:
            d.booked_by = b_cf[CUSTOM_BOOKED_BY][:64]
        
        #Send customer email copy of invoice? (265)
        CUSTOM_EMAIL_INVOICE = current_app.config['CUSTOM_EMAIL_INVOICE']
        if CUSTOM_EMAIL_INVOICE and CUSTOM_EMAIL_INVOICE in b_cf:
            d.invoice_tobe_emailed = b_cf.get(CUSTOM_EMAIL_INVOICE)
        
        #Name for Invoice (267)
        CUSTOM_INVOICE_NAME = current_app.config['CUSTOM_INVOICE_NAME']
        if CUSTOM_INVOICE_NAME and CUSTOM_INVOICE_NAME in b_cf:
            d.invoice_name = b_cf.get(CUSTOM_INVOICE_NAME)[:128]
        
        #If NDIS: Who Pays For Your Service? (263)
        CUSTOM_WHO_PAYS = current_app.config['CUSTOM_WHO_PAYS']
        if CUSTOM_W4PAYS and CUSTOM_WHO_PAYS in b_cf:
            d.NDIS_who_pays = b_cf.get(CUSTOM_WHO_PAYS)[:64]
        
        #Email For Invoices (NDIS and Bank Transfer Only) (261)
        CUSTOM_INVOICE_EMAIL_ADDRESS = current_app.config['CUSTOM_INVOICE_EMAIL_ADDRESS']
        if CUSTOM_INVOICE_EMAIL_ADDRESS and CUSTOM_INVOICE_EMAIL_ADDRESS in b_cf:
            d.invoice_email = b_cf[CUSTOM_INVOICE_EMAIL_ADDRESS][:64]
        
        #How long since your last lawn service?
        CUSTOM_LAST_SERVICE = current_app.config['CUSTOM_LAST_SERVICE']
        if CUSTOM_LAST_SERVICE and CUSTOM_LAST_SERVICE in b_cf:
            d.last_service = b_cf.get(CUSTOM_LAST_SERVICE)
        
        #Invoice Reference (e.g. NDIS #) (262)
        CUSTOM_INVOICE_REFERENCE = current_app.config['CUSTOM_INVOICE_REFERENCE']
        if CUSTOM_INVOICE_REFERENCE and CUSTOM_INVOICE_REFERENCE in b_cf:
            d.invoice_reference = b_cf.get(CUSTOM_INVOICE_REFERENCE)
        
        #Invoice Reference (e.g. NDIS #) (262)
        CUSTOM_INVOICE_REFERENCE_EXTRA = current_app.config['CUSTOM_INVOICE_REFERENCE_EXTRA']
        if CUSTOM_INVOICE_REFERENCE_EXTRA and CUSTOM_INVOICE_REFERENCE_EXTRA in b_cf:
            d.invoice_reference_extra = b_cf.get(CUSTOM_INVOICE_REFERENCE_EXTRA)
        
        #NDIS Number (301)
        CUSTOM_NDIS_NUMBER = current_app.config['CUSTOM_NDIS_NUMBER']
        if CUSTOM_NDIS_NUMBER and CUSTOM_NDIS_NUMBER in b_cf:
            d.NDIS_reference = b_cf.get(CUSTOM_NDIS_NUMBER)
        
        #Is your date & time flexible? (266)
        CUSTOM_FLEXIBLE =  current_app.config['CUSTOM_FLEXIBLE']
        if CUSTOM_FLEXIBLE and CUSTOM_FLEXIBLE in b_cf:
            d.flexible_date_time = b_cf.get(CUSTOM_FLEXIBLE)
            
        # If hourly what would you like us to focus on? -- ONLY M2M
        CUSTOM_HOURLY_NOTES = current_app.config['CUSTOM_HOURLY_NOTES']
        if CUSTOM_HOURLY_NOTES and CUSTOM_HOURLY_NOTES in b_cf:
            d.hourly_notes = b_cf.get(CUSTOM_HOURLY_NOTES)
            
        
    return d
