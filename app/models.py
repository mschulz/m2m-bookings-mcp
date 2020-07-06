# app/models

import json
from datetime import datetime

from app import db
#from sqlalchemy import and_
#from sqlalchemy.dialects.postgresql import JSON

from flask import request, current_app

class Booking(db.Model):
    '''
        Booking class holds all the data for the current booking. 
        Data could come from the database or from an incoming zap.
    '''
    __tablename__ = 'bookings'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Uniquely identifies this booking
    booking_id = db.Column(db.Integer, index=False, unique=True)
    _created_at = db.Column(db.DateTime(timezone=True), index=False, unique=False)
    _updated_at = db.Column(db.DateTime(timezone=True), index=False, unique=False)
    service_time = db.Column(db.String(64), index=False, unique=False)
    _service_date = db.Column(db.Date, index=False, unique=False)
    _final_price = db.Column(db.Integer, index=False, unique=False)
    _extras_price = db.Column(db.Integer, index=False, unique=False)
    _subtotal =  db.Column(db.Integer, index=False, unique=False)
    _tip = db.Column(db.Integer, index=False, unique=False)
    payment_method = db.Column(db.String(64), index=False, unique=False)
    rating_value = db.Column(db.Integer, index=False, unique=False)
    rating_text = db.Column(db.Text(), index=False, unique=False)
    rating_comment = db.Column(db.Text(), index=False, unique=False)
    _rating_comment_presence = db.Column(db.Boolean, index=False, unique=False)
    frequency = db.Column(db.String(64), index=False, unique=False)
    discount_code = db.Column(db.String(64), index=False, unique=False)
    _discount_from_code = db.Column(db.Integer, index=False, unique=False)
    _giftcard_amount = db.Column(db.Integer, index=False, unique=False)
    _teams_assigned = db.Column(db.String(80), index=False, unique=False)
    ### Pointed to by assigned team or teams
    ### teams = db.relationship("Team", secondary=booking_team_association, lazy='subquery',
    ###    backref=db.backref('team_bookings', lazy=True))
    _teams_assigned_ids = db.Column(db.String(80), index=False, unique=False)
    _team_share = db.Column(db.String(80), index=False, unique=False)
    _team_share_total = db.Column(db.Integer, index=False, unique=False)
    team_has_key = db.Column(db.Boolean, index=False, unique=False)
    team_requested = db.Column(db.String(80), index=False, unique=False)
    created_by =  db.Column(db.String(64), index=False, unique=False)
    _next_booking_date = db.Column(db.DateTime(timezone=True), index=False, unique=False)
    service_category = db.Column(db.String(64), index=False, unique=False)
    service = db.Column(db.String(64), index=False, unique=False)
    customer_notes = db.Column(db.Text(), index=False, unique=False)
    staff_notes = db.Column(db.Text(), index=False, unique=False)
    _customer_id =db.Column(db.Integer, index=False, unique=False)
    ### Points to the unique customer for this booking
    ### customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'))
    cancellation_type = db.Column(db.String(64), index=False, unique=False)
    cancelled_by = db.Column(db.String(64), index=False, unique=False)
    _cancellation_date = db.Column(db.Date, index=False, unique=False, nullable=True)
    cancellation_reason = db.Column(db.Text(), index=False, unique=False)
    _price_adjustment = db.Column(db.Integer, index=False, unique=False)
    price_adjustment_comment =  db.Column(db.Text(), index=False, unique=False)
    booking_status = db.Column(db.String(64), index=False, unique=False)
    _is_first_recurring = db.Column(db.Boolean, index=False, unique=False)
    _is_new_customer = db.Column(db.Boolean, index=False, unique=False)
    extras = db.Column(db.Text(), index=False, unique=False)
    source = db.Column(db.String(64), index=False, unique=False)
    _sms_notifications_enabled = db.Column(db.Boolean, index=False, unique=False)
    pricing_parameters = db.Column(db.String(64), index=False, unique=False)
    _pricing_parameters_price = db.Column(db.Integer, index=False, unique=False)

    # Customer data
    address = db.Column(db.String(64), index=False, unique=False)
    last_name = db.Column(db.String(64), index=False, unique=False)
    city = db.Column(db.String(64), index=False, unique=False)
    state = db.Column(db.String(32), index=False, unique=False)
    first_name = db.Column(db.String(64), index=False, unique=False)
    company_name = db.Column(db.String(64), index=False, unique=False)
    email = db.Column(db.String(64), index=False, unique=False)
    name = db.Column(db.String(64), index=False, unique=False)
    phone = db.Column(db.String(64), index=False, unique=False)
    postcode = db.Column(db.String(16), index=False, unique=False)
    location = db.Column(db.String(64), index=False, unique=False)
    
    # Custom field data
    
    ## How did you find Maid2Match
    lead_source =  db.Column(db.String(64), index=False, unique=False)
    # Which team member booked this clean in?
    booked_by =  db.Column(db.String(64), index=False, unique=False)
    #Is your date & time flexible? (266)
    flexible_date_time = db.Column(db.String(64), index=False, unique=False)
    #Name for Invoice (267)
    invoice_name = db.Column(db.String(64), index=False, unique=False)
    #Email For Invoices (NDIS and Bank Transfer Only) (261)
    invoice_email = db.Column(db.String(64), index=False, unique=False)
    #Invoice Reference (e.g. NDIS #) (262)
    invoice_reference = db.Column(db.String(16), index=False, unique=False)
    #Send customer email copy of invoice? (265)
    _invoice_tobe_emailed = db.Column(db.Boolean, index=False, unique=False)
    #If NDIS: Who Pays For Your Service? (263)
    NDIS_who_pays = db.Column(db.String(16), index=False, unique=False)
    #NDIS Number (301)
    NDIS_reference = db.Column(db.String(16), index=False, unique=False)
    
    
    def __repr__(self):
        return f'<Booking {self.id}>'
        
    def to_dict(self):
        return {col.name: getattr(self, col.name) for col in self.__table__.columns}
    
    @property
    def created_at(self):
            return self._created_at
            
    @created_at.setter
    def created_at(self, val):
        # "2018-10-24T13:10:19+10:00"
        if val is not None:
            try:
                self._created_at = datetime.strptime(val, "%Y-%m-%dT%H:%M:%S%z")
            except ValueError as e:
                current_app.logger.error(f'created_at error ({val}): {e}')
    
    @property
    def updated_at(self):
        return self._updated_at
    
    @updated_at.setter
    def updated_at(self, val):
        # "2018-10-25T11:06:33+10:00"
        if val is not None:
            try:
                self._updated_at = datetime.strptime(val, "%Y-%m-%dT%H:%M:%S%z")
            except ValueError as e:
                current_app.logger.error(f'updated_at error ({val}): {e}')

    @property
    def service_date(self):
        return self._service_date
    
    @service_date.setter
    def service_date(self, val):
        """
            Convert date stamp to datetime.  
            NOTE:
                This won't have any timezone information.
                this is held in the "service_date_timestamp": "2018-10-26T12:00:00+10:00"
        """
        # "2018-10-26" 
        if val is not None:
            try:
                self._service_date = datetime.strptime(val, "%Y-%m-%d")
            except ValueError as e:
                current_app.logger.error(f'service_date error ({val}): {e}')
    
    @property
    def final_price(self):
        return self._final_price
    
    @final_price.setter
    def final_price(self, val):
        if val is not None:
            self._final_price = dollar_string_to_int(val)

    @property
    def extras_price(self):
        return self._extras_price
    
    @extras_price.setter
    def extras_price(self, val):
        if val is not None:
            self._extras_price= dollar_string_to_int(val)

    @property
    def subtotal(self):
        return self._subtotal
    
    @subtotal.setter
    def subtotal(self, val):
        if val is not None:
            self._subtotal = dollar_string_to_int(val)
    
    @property
    def final_amount(self):
        return self._final_amount
    
    @final_amount.setter
    def final_amount(self, val):
        if val is not None:
            self._final_amount = dollar_string_to_int(val)
    
    @property
    def tip(self):
        return self._tip
    
    @tip.setter
    def tip(self, val):
        if val is not None:
            self._tip = dollar_string_to_int(val)
    
    @property
    def rating_comment_presence(self):
        return self._rating_comment_presence
    
    @rating_comment_presence.setter
    def rating_comment_presence(self, val):
        if val is not None:
            self._rating_comment_presence = string_to_boolean(val)

    @property
    def discount_from_code(self):
        return self._discount_from_code
    
    @discount_from_code.setter
    def discount_from_code(self, val):
        if val is not None:
            self._discount_from_code = dollar_string_to_int(val)
    
    @property
    def giftcard_amount(self):
        return self._giftcard_amount
    
    @giftcard_amount.setter
    def giftcard_amount(self, val):
        if val is not None:
            self._giftcard_amount = dollar_string_to_int(val)   
   
    @property
    def teams_assigned(self):
        return self._teams_assigned
    
    @teams_assigned.setter
    def teams_assigned(self, val):
        # "team_details": "[{u'phone': u'+6 (142) 695-8397', u'first_name': u'Irene & Yong',
        # u'last_name': u'', u'image_url': u'', u'name': u'Irene & Yong', u'title': u'Team Euclid',
        #  u'id': u'8447'}]", 
        if val is not None:
            team_list_dict = json.loads(val.replace("'", '"').replace('u"', '"'))
            team_list = [item['title'] for item in team_list_dict]
            self._teams_assigned = ','.join(team_list)
   
    @property
    def teams_assigned_ids(self):
        return self._teams_assigned_ids
    
    @teams_assigned_ids.setter
    def teams_assigned_ids(self, val):
        # "team_details": "[{u'phone': u'+6 (142) 695-8397', u'first_name': u'Irene & Yong',
        # u'last_name': u'', u'image_url': u'', u'name': u'Irene & Yong', u'title': u'Team Euclid',
        #  u'id': u'8447'}]",
        if val is not None:
            team_list_dict = json.loads(val.replace("'", '"').replace('u"', '"'))
            team_list_ids = [item['id'] for item in team_list_dict]
            self._teams_assigned_ids = ','.join(team_list_ids)

    @property
    def team_share(self):
        return self._team_share
    
    @team_share.setter
    def team_share(self, val):
        #  "team_share_amount": "Team Euclid - $67.64"
        if val:
            try:
                amt = val.split(' - ')[1]
                self._team_share =  amt.replace('$','').replace('.','')
            except IndexError as e:
                current_app.logger.error(f'team share error ({val}): {e}')
    
    @property
    def team_share_total(self):
        return self._team_share_total
    
    @team_share_total.setter
    def team_share_total(self, val):
        # "Team Euclid - $67.64", 
        if val:
            try:
                amt = val.split(' - ')[1]
                self._team_share_total = amt.replace('$','').replace('.','')
            except IndexError as e:
                current_app.logger.error(f'team share total error ({val}): {e}')
                
    
    @property
    def team_has_key(self):
        return self._team_has_key
    
    @team_has_key.setter
    def team_has_key(self, val):
        if val is not None:
            self._team_has_key = string_to_boolean(val)
    
    @property
    def next_booking_date(self):
        return self._next_booking_date
    
    @next_booking_date.setter
    def next_booking_date(self, val):
        # "2018-10-25T11:06:33+10:00"
        if val is not None:
            try:
                self._next_booking_date = datetime.strptime(val, "%Y-%m-%dT%H:%M:%S%z")
            except ValueError as e:
                current_app.logger.error(f'next_booking_date error ({val}): {e}')
   
    @property
    def customer_id(self):
        return self._customer_id
    
    @customer_id.setter
    def customer_id(self, val):
        #  { 
        #       "last_name": "Nall", 
        #       "updated_at": "2018-10-24T13:10:19+10:00", 
        #       "id": "8674", ...
        if val is not None:
            self._customer_id = int(val['id'])
    
    @property
    def cancellation_date(self):
        return self._cancellation_date
    
    @cancellation_date.setter
    def cancellation_date(self, val):
        # "2018-10-25T11:06:33+10:00"
        if val:
            try:
                self._cancellation_date = datetime.strptime(val, "%d/%m/%Y").date()
            except ValueError as e:
                current_app.logger.error(f'cancellation_date error: "{val}" leads to error: {e}')
    
    @property
    def price_adjustment(self):
        return self._price_adjustment
    
    @price_adjustment.setter
    def price_adjustment(self, val):
        # "2018-10-25T11:06:33+10:00"
        if val is not None:
            try:
                self._price_adjustment = dollar_string_to_int(val)
            except ValueError as e:
                current_app.logger.error(f'price_adjustment error ({val}): {e}')
 
    @property
    def is_first_recurring(self):
        return self._is_first_recurring

    @is_first_recurring.setter
    def is_first_recurring(self, val):
        if val is not None:
            self._is_first_recurring= string_to_boolean(val)
    
    @property
    def is_new_customer(self):
        return self._is_new_customer
    
    @is_new_customer.setter
    def is_new_customer(self, val):
        if val is not None:
            self._is_new_customer = string_to_boolean(val)
    
    @property
    def invoice_tobe_emailed(self):
        return self._invoice_tobe_emailed
    
    @invoice_tobe_emailed.setter
    def invoice_tobe_emailed(self, val):
        if val is not None:
            self._invoice_tobe_emailed = string_to_boolean(val)
    
    @property
    def sms_notifications_enabled(self):
        return self._sms_notifications_enabled
    
    @sms_notifications_enabled.setter
    def sms_notifications_enabled(self, val):
        if val is not None:
            self._sms_notifications_enabled = string_to_boolean(val)
    
    @property
    def pricing_parameters_price(self):
        return self._pricing_parameters_price
    
    @pricing_parameters_price.setter
    def pricing_parameters_price(self, val):
        # "2018-10-25T11:06:33+10:00"
        if val is not None:
            try:
                self._pricing_parameters_price = dollar_string_to_int(val)
            except ValueError as e:
                current_app.logger.error(f'price_adjustment error ({val}): {e}')


def string_to_boolean(val):
    return val.lower() in ['true', 'yes']

def dollar_string_to_int(val):
    return  int(val.replace('$','').replace('.','')) 


def import_dict(d, b):
    booking_keys = b.keys()
    if 'custom_fields' in booking_keys:
        custom_field_keys = b['custom_fields'].keys()
    
    d.booking_id = b['id'] if 'id' in booking_keys else None
    d.created_at = b['created_at'] if 'created_at' in booking_keys else None
    d.updated_at = b['updated_at'] if 'updated_at' in booking_keys else None
    d.service_time = b['service_time'] if 'service_time' in booking_keys else None
    d.service_date = b['service_date'] if 'service_date' in booking_keys else None
    d.final_price = b['final_price'] if 'final_price' in booking_keys else None
    d.extras_price = b['extras_price'] if 'extras_price' in booking_keys else None
    d.subtotal = b['subtotal'] if 'subtotal' in booking_keys else None
    d.tip = b['tip'] if 'tip' in booking_keys else None
    d.payment_method = b['payment_method'] if 'payment_method' in booking_keys else None
    d.rating_value = b['rating_value'] if 'rating_value' in booking_keys else None
    d.rating_text = b['rating_text'] if 'rating_text' in booking_keys else None
    d.rating_comment = b['rating_comment'] if 'rating_comment' in booking_keys else None
    d.rating_comment_presence = b['rating_comment_presence'] if 'rating_comment_presence' in booking_keys else None
    d.frequency = b['frequency'] if 'frequency' in booking_keys else None
    d.discount_code = b['discount_code'] if 'discount_code' in booking_keys else None
    d.discount_from_code = b['discount_amount'] if 'discount_amount' in booking_keys else None
    d.giftcard_amount = b['giftcard_amount'] if 'giftcard_amount' in booking_keys else None
    d.teams_assigned = b['team_details'] if 'team_details' in booking_keys else None
    ### Pointed to by assigned team or teams
    ### teams = db.relationship("Team", secondary=booking_team_association, lazy='subquery',
    ###    backref=db.backref('team_bookings', lazy=True))
    d.teams_assigned_ids = b['team_details'] if 'team_details' in booking_keys else None
    d.team_share = b['team_share_amount'] if 'team_share_amount' in booking_keys else None
    d.team_share_total = b['team_share_total'] if 'team_share_total' in booking_keys else None
    d.team_has_key = b['team_has_key'] if 'team_has_key' in booking_keys else None
    d.team_requested = b['team_requested'] if 'team_requested' in booking_keys else None
    d.created_by = b['created_by'] if 'created_by' in booking_keys else None
    d.next_booking_date = b['next_booking_date'] if 'next_booking_date' in booking_keys else None
    d.service_category = b['service_category'] if 'service_category' in booking_keys else 'House Clean'
    d.service = b['service'] if 'service' in booking_keys else None
    d.customer_notes = b['customer_notes'] if 'customer_notes' in booking_keys else None
    d.staff_notes = b['staff_notes'] if 'staff_notes' in booking_keys else None
    d.customer_id = b['customer'] if 'customer' in booking_keys else None
    ### Points to the unique customer for this booking
    ### customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'))
    d.cancellation_type = b['cancellation_type'] if 'cancellation_type' in booking_keys else None
    d.cancelled_by = b['cancelled_by'] if 'cancelled_by' in booking_keys else None
    d.cancellation_date = b['cancellation_date'] if 'cancellation_date' in booking_keys else None
    d.cancellation_reason = b['cancellation_reason'] if 'cancellation_reason' in booking_keys else None
    d.price_adjustment = b['price_adjustment'] if 'price_adjustment' in booking_keys else None
    d.price_adjustment_comment = b['price_adjustment_comment'] if 'price_adjustment_comment' in booking_keys else None
    d.booking_status = b['booking_status'] if 'booking_status' in booking_keys else None
    d.is_first_recurring = b['is_first_recurring'] if 'is_first_recurring' in booking_keys else None
    d.is_new_customer = b['is_new_customer'] if 'is_new_customer' in booking_keys else None
    d.extras = b['extras'] if 'extras' in booking_keys else None
    d.source = b['source'] if 'source' in booking_keys else None
    d.state = b['state'] if 'state' in booking_keys else None
    d.sms_notifications_enabled = b['sms_notifications_enabled'] if 'sms_notifications_enabled' in booking_keys else None
    d.pricing_parameters = b['pricing_parameters'] if 'pricing_parameters' in booking_keys else None
    d.pricing_parameters_price = b['pricing_parameters_price'] if 'pricing_parameters_price' in booking_keys else None

    # Customer data
    d.address = b['address'] if 'address' in booking_keys else None
    d.last_name = b['last_name'] if 'last_name' in booking_keys else None
    d.city = b['city'] if 'city' in booking_keys else None
    d.first_name = b['first_name'] if 'first_name' in booking_keys else None
    d.company_name = b['company_name'] if 'company_name' in booking_keys else None
    d.email = b['email'] if 'email' in booking_keys else None
    d.name = b['name'] if 'name' in booking_keys else None
    d.phone = b['phone'] if 'phone' in booking_keys else None
    d.postcode = b['zip'] if 'zip' in booking_keys else None
    d.location = b['location'] if 'location' in booking_keys else None
    
    # Custom field data
    
    if 'custom_fields' in booking_keys:
        ## How did you find Maid2Match
        d.lead_source = b["custom_fields"]['drop_down:65c938ba-a125-48ba-a21f-9fb34350ab24'] if 'drop_down:65c938ba-a125-48ba-a21f-9fb34350ab24' in custom_field_keys else None
        # Which team member booked this clean in?
        d.booked_by = b["custom_fields"]['single_line:a3a07fee-eb4f-42ae-ab31-9977d4d1acf9'] if 'single_line:a3a07fee-eb4f-42ae-ab31-9977d4d1acf9' in custom_field_keys else None
        #Is your date & time flexible? (266)
        d.flexible_date_time = b["custom_fields"]['drop_down:f5c6492a-82cc-41cf-8e0b-5390bea7d71b'] if 'drop_down:f5c6492a-82cc-41cf-8e0b-5390bea7d71b' in custom_field_keys else None
        #Name for Invoice (267)
        d.invoice_name = b["custom_fields"]['single_line:b382b477-5ddd-498e-ba36-74d55c7f0146'] if 'single_line:b382b477-5ddd-498e-ba36-74d55c7f0146' in custom_field_keys else None
        #Email For Invoices (NDIS and Bank Transfer Only) (261)
        d.invoice_email = b["custom_fields"]['single_line:c131935b-e8cf-4ef9-b6ff-6068a674c49d'] if 'single_line:c131935b-e8cf-4ef9-b6ff-6068a674c49d' in custom_field_keys else None
        #Invoice Reference (e.g. NDIS #) (262)
        d.invoice_reference =b["custom_fields"]['single_line:73238370-80d8-4cbe-8577-74e3ade200a0'] if 'single_line:73238370-80d8-4cbe-8577-74e3ade200a0' in custom_field_keys else None
        #Send customer email copy of invoice? (265)
        d.invoice_tobe_emailed = b["custom_fields"]['drop_down:a255d2c7-fb9a-4fa8-beb6-a91bc1ef6fed'] if 'drop_down:a255d2c7-fb9a-4fa8-beb6-a91bc1ef6fed' in custom_field_keys else None
        #If NDIS: Who Pays For Your Service? (263)
        d.NDIS_who_pays =b["custom_fields"]['drop_down:5842d47d-52c9-4cff-ba42-f5b90ada72e5'] if 'drop_down:5842d47d-52c9-4cff-ba42-f5b90ada72e5' in custom_field_keys else None
        #NDIS Number (301)
        d.NDIS_reference = b["custom_fields"]['single_line:2b738d28-6c2c-4850-ae47-2c4902da9d8d'] if 'single_line:2b738d28-6c2c-4850-ae47-2c4902da9d8d' in custom_field_keys else None

    return d
    