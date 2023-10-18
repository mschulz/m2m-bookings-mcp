# app/models

import json
from datetime import datetime, date
import dateutil.parser
import ast

from app import db
from sqlalchemy.ext.hybrid import hybrid_property

from flask import request, current_app
from app.email import send_error_email
from app.locations import get_location
from app.local_date_time import utc_to_local


class Booking(db.Model):
    '''
        Booking class holds all the data for the current booking. 
        Data could come from the database or from an incoming zap.
    '''
    __tablename__ = 'bookings'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Uniquely identifies this booking
    booking_id = db.Column(db.Integer, index=True, unique=True)
    _created_at = db.Column(db.DateTime(timezone=True), index=False, unique=False)
    _updated_at = db.Column(db.DateTime(timezone=True), index=False, unique=False)
    service_time = db.Column(db.String(64), index=False, unique=False)
    _service_date = db.Column(db.Date, index=False, unique=False)
    _final_price = db.Column(db.Integer, index=False, unique=False)
    _extras_price = db.Column(db.Integer, index=False, unique=False)
    _subtotal =  db.Column(db.Integer, index=False, unique=False)
    _tip = db.Column(db.Integer, index=False, unique=False)

    payment_method = db.Column(db.String(64), index=False, unique=False)
    _rating_value = db.Column(db.Integer, index=False, unique=False)
    rating_text = db.Column(db.Text(), index=False, unique=False)
    rating_comment = db.Column(db.Text(), index=False, unique=False)
    _rating_comment_presence = db.Column(db.Boolean, index=False, unique=False)
    rating_created_by = db.Column(db.String(64), index=False, unique=False)
    rating_received = db.Column(db.DateTime(timezone=True), index=False, unique=False)
    rating_modified = db.Column(db.DateTime(timezone=True), index=False, unique=False)
    rating_modified_by = db.Column(db.String(64), index=False, unique=False)

    frequency = db.Column(db.String(64), index=False, unique=False)
    discount_code = db.Column(db.String(64), index=False, unique=False)
    _discount_from_code = db.Column(db.Integer, index=False, unique=False)
    _giftcard_amount = db.Column(db.Integer, index=False, unique=False)
    _teams_assigned = db.Column(db.String(80), index=False, unique=False)
    ### Pointed to by assigned team or teams
    ### teams = db.relationship("Team", secondary=booking_team_association, lazy='subquery',
    ###    backref=db.backref('team_bookings', lazy=True))
    _teams_assigned_ids = db.Column(db.String(80), index=False, unique=False)
    _team_share = db.Column(db.Integer, index=False, unique=False)
    #_team_share_total = db.Column(db.Integer, index=False, unique=False)
    team_share_summary = db.Column(db.String(128), index=False, unique=False)
    #team_has_key = db.Column(db.Boolean, index=False, unique=False)
    team_has_key = db.Column(db.String(64), index=False, unique=False)
    team_requested = db.Column(db.String(80), index=False, unique=False)
    created_by =  db.Column(db.String(64), index=False, unique=False)
    _next_booking_date = db.Column(db.DateTime(timezone=True), index=False, unique=False)
    service_category = db.Column(db.String(64), index=False, unique=False)
    service = db.Column(db.String(128), index=False, unique=False)
    customer_notes = db.Column(db.Text(), index=False, unique=False)
    staff_notes = db.Column(db.Text(), index=False, unique=False)
    _customer_id = db.Column(db.Integer, index=False, unique=False)
    ### Points to the unique customer for this booking
    ### customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'))
    
    cancellation_type = db.Column(db.String(64), index=False, unique=False)
    cancelled_by = db.Column(db.String(64), index=False, unique=False)
    _cancellation_date = db.Column(db.Date, index=False, unique=False, nullable=True)
    cancellation_reason = db.Column(db.Text(), index=False, unique=False)
    _cancellation_fee = db.Column(db.Integer, index=False, unique=False)
    _cancellation_datetime = db.Column(db.DateTime(timezone=True), index=False, unique=False)   ########### NEW #########
    
    _price_adjustment = db.Column(db.Integer, index=False, unique=False)
    price_adjustment_comment =  db.Column(db.Text(), index=False, unique=False)
    booking_status = db.Column(db.String(64), index=False, unique=False)
    _is_first_recurring = db.Column(db.Boolean, index=False, unique=False)
    _is_new_customer = db.Column(db.Boolean, index=False, unique=False)
    # Added these next two columns to keep a premanent record of is_first_recurring and is_new_customer
    was_first_recurring = db.Column(db.Boolean, index=False, unique=False, default=False)
    was_new_customer = db.Column(db.Boolean, index=False, unique=False, default=False)
    extras = db.Column(db.Text(), index=False, unique=False)
    source = db.Column(db.String(64), index=False, unique=False)
    _sms_notifications_enabled = db.Column(db.Boolean, index=False, unique=False)
    pricing_parameters = db.Column(db.String(64), index=False, unique=False)
    _pricing_parameters_price = db.Column(db.Integer, index=False, unique=False)

    # Customer data
    address = db.Column(db.String(128), index=False, unique=False)
    last_name = db.Column(db.String(64), index=False, unique=False)
    city = db.Column(db.String(64), index=False, unique=False)
    state = db.Column(db.String(32), index=False, unique=False)
    first_name = db.Column(db.String(64), index=False, unique=False)
    company_name = db.Column(db.String(64), index=False, unique=False)
    email = db.Column(db.String(64), index=False, unique=False)
    name = db.Column(db.String(128), index=False, unique=False)
    phone = db.Column(db.String(64), index=False, unique=False)
    postcode = db.Column(db.String(16), index=False, unique=False)
    location = db.Column(db.String(64), index=False, unique=False)
    
    # Custom field data
    
    ## How did you find Maid2Match
    lead_source =  db.Column(db.String(64), index=False, unique=False)
    # Which team member booked this clean in?
    booked_by =  db.Column(db.String(64), index=False, unique=False)
    #Send customer email copy of invoice? (265)
    _invoice_tobe_emailed = db.Column(db.Boolean, index=False, unique=False)
    #Name for Invoice (267)
    invoice_name = db.Column(db.String(128), index=False, unique=False)
    #If NDIS: Who Pays For Your Service? (263)
    NDIS_who_pays = db.Column(db.String(64), index=False, unique=False)
    #Email For Invoices (NDIS and Bank Transfer Only) (261)
    invoice_email = db.Column(db.String(64), index=False, unique=False)
    # How long since your last lawn service? 
    last_service = db.Column(db.String(80), index=False, unique=False)
    #Invoice Reference (e.g. NDIS #) (262)
    invoice_reference = db.Column(db.String(80), index=False, unique=False)
    #Invoice Reference (e.g. NDIS #) (262)
    invoice_reference_extra = db.Column(db.String(80), index=False, unique=False)
    #NDIS Number (301)
    NDIS_reference = db.Column(db.String(64), index=False, unique=False)
    #Is your date & time flexible? (266)
    flexible_date_time = db.Column(db.String(64), index=False, unique=False)
    # If hourly what would you like us to focus on?
    hourly_notes = db.Column(db.Text(), index=False, unique=False)
    
    def __repr__(self):
        return f'<Booking {self.id}>'
        
    def to_dict(self):
        return {col.name: getattr(self, col.name) for col in self.__table__.columns}
    
    def to_json(self):
        def json_serial(obj):
            """JSON serializer for objects not serializable by default json code"""
            if isinstance(obj, (datetime, date)):
                return obj.isoformat()
            #raise TypeError ("Type {type(obj)} not serializable" )
            return obj
        
        d = self.to_dict()
        return {k:json_serial(v) for k,v in d.items()}
    
    @hybrid_property
    def created_at(self):
        
        print(f'created_at={self._created_at}')
        
        return utc_to_local(self._created_at)

    @staticmethod
    def _unmangle_datetime(val):
        try:
            if 'Z' in val:
                return dateutil.parser.isoparse(val)
            elif 'am' in val or 'pm' in val:
                return datetime.strptime(val, "%d/%m/%Y %I:%M%p")
            elif 'T' in val:
                # "2018-10-25T11:06:33+10:00"
                return datetime.strptime(val, "%Y-%m-%dT%H:%M:%S%z")
            elif ' ' in val:
                # '17/07/2020 21:01'
                return datetime.strptime(val, "%d/%m/%Y %H:%M")
            elif '/' in val:
                return datetime.strptime(val, "%d/%m/%Y")
            else:
                return datetime.strptime(val, "%Y-%m-%d")
        except ValueError as e:
            current_app.logger.error(f'service_date error ({val}): {e}')
        
    @created_at.setter
    def created_at(self, val):
        if val is not None:
            try:
                self._created_at = self._unmangle_datetime(val)
            except ValueError as e:
                current_app.logger.error(f'created_at error ({val}): {e}')
    
    @hybrid_property
    def updated_at(self):
        return utc_to_local(self._updated_at)
    
    @updated_at.setter
    def updated_at(self, val):
        if val is not None:
            try:
                self._updated_at = self._unmangle_datetime(val)
            except ValueError as e:
                current_app.logger.error(f'updated_at error ({val}): {e}')

    @hybrid_property
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
                if '/' in val:
                    self._service_date = datetime.strptime(val, "%d/%m/%Y")
                else:
                    self._service_date = datetime.strptime(val, "%Y-%m-%d")
            except ValueError as e:
                current_app.logger.error(f'service_date error ({val}): {e}')
    
    @hybrid_property
    def final_price(self):
        return self._final_price
    
    @final_price.setter
    def final_price(self, val):
        if val is not None:
            self._final_price = dollar_string_to_int(val)

    @hybrid_property
    def extras_price(self):
        return self._extras_price
    
    @extras_price.setter
    def extras_price(self, val):
        if val is not None:
            self._extras_price= dollar_string_to_int(val)

    @hybrid_property
    def subtotal(self):
        return self._subtotal
    
    @subtotal.setter
    def subtotal(self, val):
        if val is not None:
            self._subtotal = dollar_string_to_int(val)
    
    @hybrid_property
    def final_amount(self):
        return self._final_amount
    
    @final_amount.setter
    def final_amount(self, val):
        if val is not None:
            self._final_amount = dollar_string_to_int(val)
    
    @hybrid_property
    def tip(self):
        return self._tip
    
    @tip.setter
    def tip(self, val):
        if val is not None:
            self._tip = dollar_string_to_int(val)
    
    @hybrid_property
    def rating_value(self):
        return self._rating_value
    
    @rating_value.setter
    def rating_value(self, val):
        if val is not None:
            if isinstance(val, str):
                if len(val) == 0:
                    self._rating_value = None
                else:
                    self._rating_value = int(val)
            else:
                self._rating_value = val
                
    
    @hybrid_property
    def rating_comment_presence(self):
        return self._rating_comment_presence
    
    @rating_comment_presence.setter
    def rating_comment_presence(self, val):
        if val is not None:
            self._rating_comment_presence = string_to_boolean(val)

    @hybrid_property
    def discount_from_code(self):
        return self._discount_from_code
    
    @discount_from_code.setter
    def discount_from_code(self, val):
        if val is not None:
            self._discount_from_code = dollar_string_to_int(val)
    
    @hybrid_property
    def giftcard_amount(self):
        return self._giftcard_amount
    
    @giftcard_amount.setter
    def giftcard_amount(self, val):
        if val is not None:
            self._giftcard_amount = dollar_string_to_int(val)   
   
    @hybrid_property
    def teams_assigned(self):
        return self._teams_assigned

    def get_team_list(self, val, key_str):
        if val:
            # Convert the string into a dictionary
            team_details = ast.literal_eval(val)
            team_details_list = [item[key_str] for item in team_details]
            assigned_teams_string = ','.join(team_details_list)
            return assigned_teams_string
        else:
            return ''

    @teams_assigned.setter
    def teams_assigned(self, val):
        # "team_details": "[{u'phone': u'+6 (142) 695-8397', u'first_name': u'Irene & Yong',
        # u'last_name': u'', u'image_url': u'', u'name': u'Irene & Yong', u'title': u'Team Euclid',
        #  u'id': u'8447'}]", 
        if val is not None:
            self._teams_assigned = self.get_team_list(val, 'title')
   
    @hybrid_property
    def teams_assigned_ids(self):
        return self._teams_assigned_ids

    @teams_assigned_ids.setter
    def teams_assigned_ids(self, val):
        # "team_details": "[{u'phone': u'+6 (142) 695-8397', u'first_name': u'Irene & Yong',
        # u'last_name': u'', u'image_url': u'', u'name': u'Irene & Yong', u'title': u'Team Euclid',
        #  u'id': u'8447'}]",
        if val is not None:
            self._teams_assigned_ids = self.get_team_list(val, 'id')

    @hybrid_property
    def team_share(self):
        return self._team_share
    
    @team_share.setter
    def team_share(self, val):
        if val and ',' not in val:
            try:
                if '-' in val:
                    #  "team_share_amount": "Team Euclid - $67.64"
                    if '-' in val:
                        self._team_share =  dollar_string_to_int(val.split(' - ')[-1])
                    else:
                        self._team_share =  dollar_string_to_int(val.split(': ')[-1])
                else:
                    self._team_share =  dollar_string_to_int(val)
            except IndexError as e:
                current_app.logger.error(f'team share error ({val}): {e}')
    
    ##########  IGNORE THIS VALUE ALTOGETHER #####################
    """@hybrid_property
    def team_share_total(self):
        return self._team_share_total
    
    @team_share_total.setter
    def team_share_total(self, val):
        # "Team Euclid - $67.64", 
        if val:
            try:
                split_char = ':' if ':' in val else '-'
                self._team_share_total =  dollar_string_to_int(val.split(split_char)[1])
            except IndexError as e:
                current_app.logger.error(f'team share total error ({val}): {e}')"""
    ##############################################################
    
    @hybrid_property
    def next_booking_date(self):
        return utc_to_local(self._next_booking_date)
    
    @next_booking_date.setter
    def next_booking_date(self, val):
        # "2018-10-25T11:06:33+10:00"
        if val is not None and len(val)> 0:
            try:
                self._next_booking_date = self._unmangle_datetime(val)
            except ValueError as e:
                current_app.logger.error(f'next_booking_date error ({val}): {e}')
   
    @hybrid_property
    def customer_id(self):
        return self._customer_id
    
    @customer_id.setter
    def customer_id(self, val):
        #  "customer": { 
        #       "last_name": "Nall", 
        #       "updated_at": "2018-10-24T13:10:19+10:00", 
        #       "id": "8674", ...
        if val is not None:
            self._customer_id = int(val)
    
    @hybrid_property
    def cancellation_date(self):
        return self._cancellation_date
    
    @cancellation_date.setter
    def cancellation_date(self, val):
        # "2018-10-25T11:06:33+10:00"
        if val:
            try:
                self._cancellation_date= self._unmangle_datetime(val).date()
            except ValueError as e:
                current_app.logger.error(f'cancellation_date error: "{val}" leads to error: {e}')

    @hybrid_property
    def cancellation_fee(self):
        return self._cancellation_fee
    
    @cancellation_fee.setter
    def cancellation_fee(self, val):
        if not isinstance(val, str):
            val = str(val)
        if val is not None and len(val) > 0:
            self._cancellation_fee= dollar_string_to_int(val)
    
    @hybrid_property
    def price_adjustment(self):
        return self._price_adjustment
    
    @price_adjustment.setter
    def price_adjustment(self, val):
        if not isinstance(val, str):
            val = str(val)
        if val is not None and len(val) > 0:
            try:
                self._price_adjustment = dollar_string_to_int(val)
            except ValueError as e:
                print(f'price_adjustment error val="{val}": error_message:{e}')
                current_app.logger.error(f'price_adjustment error val="{val}": error_message:{e}')
 
    @hybrid_property
    def is_first_recurring(self):
        return self._is_first_recurring

    @is_first_recurring.setter
    def is_first_recurring(self, val):
        self._is_first_recurring = string_to_boolean(val) if val is not None else False
            
    @hybrid_property
    def is_new_customer(self):
        return self._is_new_customer
    
    @is_new_customer.setter
    def is_new_customer(self, val):
        self._is_new_customer = string_to_boolean(val) if val is not None else False
    
    @hybrid_property
    def invoice_tobe_emailed(self):
        return self._invoice_tobe_emailed
    
    @invoice_tobe_emailed.setter
    def invoice_tobe_emailed(self, val):
        if val is not None:
            self._invoice_tobe_emailed = string_to_boolean(val)
    
    @hybrid_property
    def sms_notifications_enabled(self):
        return self._sms_notifications_enabled
    
    @sms_notifications_enabled.setter
    def sms_notifications_enabled(self, val):
        if val is not None:
            self._sms_notifications_enabled = string_to_boolean(val) if val is not None else False
    
    @hybrid_property
    def pricing_parameters_price(self):
        return self._pricing_parameters_price
    
    @pricing_parameters_price.setter
    def pricing_parameters_price(self, val):
        # "2018-10-25T11:06:33+10:00"
        if not isinstance(val, str):
            val = str(val)
        if val is not None and len(val) > 0:
            try:
                self._pricing_parameters_price = dollar_string_to_int(val)
            except ValueError as e:
                current_app.logger.error(f'pricing_parameters_price error ({val}): {e}')

def string_to_boolean(val):
    if isinstance(val, bool):
        return val
    return val.lower() in ['true', 'yes', '1']

def dollar_string_to_int(val):
    if isinstance(val, str):
        return int(val.replace('$','').replace('.',''))
    else: 
        return int(str(val).replace('$','').replace('.','')) 

def check_postcode(b, who, who_id):
    # Errors have started creeping in with invalid postcode being entered into the database.  We need to alert staff
    # to these errors so that this can be corrected ASAP
    p = b['zip'] if 'zip' in b else None
    if p:
        if p.isnumeric():
        # OK. return the postcode string
            return p
        else:
            # if it is not numeric then it is not a valid postcode
            if 'booking_id' in b:
                err_msg = f'({request.path}) Invalid postcode {p} NOT entered for booking_id "{b.booking_id}"'
            else:
                err_msg = f'({request.path}) Invalid postcode {p} NOT entered for customer_id "{who_id}"'
            current_app.logger.error(err_msg)
    # if there is no postcode provided or an error
    return None


def import_dict(d, b):
    if 'id' in b:
        d.booking_id = b['id']
    d.created_at = b['created_at'] if 'created_at' in b else None
    d.updated_at = b['updated_at'] if 'updated_at' in b else None
    d.service_time = b['service_time'] if 'service_time' in b else None
    d.service_date = b['service_date'] if 'service_date' in b else None
    d.final_price = b['final_price'] if 'final_price' in b else None
    d.extras_price = b['extras_price'] if 'extras_price' in b else None
    d.subtotal = b['subtotal'] if 'subtotal' in b else None
    d.tip = b['tip'] if 'tip' in b else None
    d.payment_method = b['payment_method'] if 'payment_method' in b else None
    #
    # Do not have the bookings from Launch27 overwrite the rating data
    # Rating data is insert ONLY rom m2m-ratings
    """d.rating_value = b['rating_value'] if 'rating_value' in b else None
    d.rating_text = b['rating_text'] if 'rating_text' in b else None
    d.rating_comment = b['rating_comment'] if 'rating_comment' in b else None
    d.rating_comment_presence = b['rating_comment_presence'] if 'rating_comment_presence' in b else None"""
    #
    d.frequency = b['frequency'] if 'frequency' in b else None
    if 'discount_code' in b:
        d.discount_code = b['discount_code']
    d.discount_from_code = b['discount_amount'] if 'discount_amount' in b else None
    d.giftcard_amount = b['giftcard_amount'] if 'giftcard_amount' in b else None
    if 'team_details' in b:
        d.teams_assigned = b['team_details']
        d.teams_assigned_ids = b['team_details']
    if 'team_share_amount' in b:
        d.team_share = b['team_share_amount']
    if 'team_share_total' in b:
        d.team_share_summary = b['team_share_total']
    d.team_has_key = b['team_has_key'] if 'team_has_key' in b else None
    d.team_requested = b['team_requested'] if 'team_requested' in b else None
    d.created_by = b['created_by'] if 'created_by' in b else None
    if 'next_booking_date' in b:
        d.next_booking_date = b['next_booking_date']
    d.service_category = b['service_category'] if 'service_category' in b else current_app.config['SERVICE_CATEGORY_DEFAULT']
    if 'service' in b:
        if len(b['service']) > 128:
            current_app.logger.error(f"booking_id: {b['id']}:: truncating service field to 128 characters {b['service']}")
        d.service = b['service'][:128]
    d.customer_notes = b['customer_notes'] if 'customer_notes' in b else None
    d.staff_notes = b['staff_notes'] if 'staff_notes' in b else None
    d.customer_id = b['customer']['id'] if 'customer' in b else None
    ### Points to the unique customer for this booking
    ### customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'))
    if 'cancellation_type' in b:
        d.cancellation_type = b['cancellation_type']
    if 'cancelled_by' in b:
        d.cancelled_by = b['cancelled_by']
    if 'cancellation_date' in b:
        d.cancellation_date = b['cancellation_date']
    if '_cancellation_datetime' in b:
        d._cancellation_datetime = b['_cancellation_datetime']
    d.cancellation_reason = b['cancellation_reason'] if 'cancellation_reason' in b else None
    if 'cancellation_fee' in b:
        d.cancellation_fee = b['cancellation_fee']
    d.price_adjustment = b['price_adjustment'] if 'price_adjustment' in b else None
    d.price_adjustment_comment = b['price_adjustment_comment'] if 'price_adjustment_comment' in b else None
    if 'booking_status' in b:
        d.booking_status = b['booking_status']
    if 'is_first_recurring' in b:
        d.is_first_recurring = b['is_first_recurring']
        if d.is_first_recurring:
            d.was_first_recurring = True
    if 'is_new_customer' in b:
        d.is_new_customer = b['is_new_customer']
        if d.is_new_customer:
            d.was_new_customer = True
    d.extras = b['extras'] if 'extras' in b else None
    d.source = b['source'] if 'source' in b else None
    d.state = b['state'] if 'state' in b else None
    d.sms_notifications_enabled = b['sms_notifications_enabled'] if 'sms_notifications_enabled' in b else None
    d.pricing_parameters = b['pricing_parameters'].replace('<br/>', ', ') if 'pricing_parameters' in b and b['pricing_parameters'] else None
    d.pricing_parameters_price = b['pricing_parameters_price'] if 'pricing_parameters_price' in b else None

    # Customer data
    d.address = b['address'] if 'address' in b else None
    d.last_name = b['last_name'] if 'last_name' in b else None
    d.city = b['city'] if 'city' in b else None
    d.first_name = b['first_name'] if 'first_name' in b else None
    d.name = b['name'] if 'name' in b else None
    d.company_name = b['company_name'] if 'company_name' in b else None

    d.email = b['email'] if 'email' in b else None
    # We are starting to see invalid email addresses creeping into the system.  This check if they are valid and sends
    # an email alerting staff to the issue.
    """if d.email:
        if not validate_email(d.email, check_mx=True, debug=False, use_blacklist=False):
            msg = f'({request.path}) Invalid email ({d.email}) entered for customer "{d.name}". Booking ID={d.booking_id}'
            current_app.logger.error(msg)"""
            
    
    d.phone = b['phone'] if 'phone' in b else None
    d.postcode = check_postcode(b, "booking_id", b['id'])
    if d.postcode:
        d.location = b['location'] if 'location' in b else get_location(d.postcode)
    
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
        if CUSTOM_WHO_PAYS and CUSTOM_WHO_PAYS in b_cf:
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


def import_cancel_dict(d, b):
    d.booking_id = b['booking_id']
    d.updated_at = b['updated_at'] if 'updated_at' in b else None ###
    if 'cancellation_type' in b:
        d.cancellation_type = b['cancellation_type']
    if 'cancelled_by' in b:
        d.cancelled_by = b['cancelled_by']
    if 'cancellation_date' in b:
        d.cancellation_date = b['cancellation_date']
    if '_cancellation_datetime' in b:
        d._cancellation_datetime = b['_cancellation_datetime']
    d.cancellation_reason = b['cancellation_reason'] if 'cancellation_reason' in b else None
    if 'cancellation_fee' in b:
        d.cancellation_fee = b['cancellation_fee']
    if 'booking_status' in b:
        d.booking_status = b['booking_status']
    if 'is_first_recurring' in b:
        d.is_first_recurring = b['is_first_recurring']
        if d.is_first_recurring:
            d.was_first_recurring = True
    if 'is_new_customer' in b:
        d.is_new_customer = b['is_new_customer']
        if d.is_new_customer:
            d.was_new_customer = True
    d.postcode = check_postcode(b, "booking_id", b['booking_id'])
    if d.postcode:
        d.location = b['location'] if 'location' in b else get_location(d.postcode)
    
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



class Customer(db.Model):
    '''
        Booking class holds all the data for the current booking. 
        Data could come from the database or from an incoming zap.
    '''
    __tablename__ = 'customer'
    
    id = db.Column(db.Integer, primary_key=True)
    
    customer_id = db.Column(db.Integer, index=True, unique=False)
    _created_at = db.Column(db.DateTime(timezone=True), index=False, unique=False)
    _updated_at = db.Column(db.DateTime(timezone=True), index=False, unique=False)

    # Customer data
    title = db.Column(db.String(16), index=False, unique=False)
    first_name = db.Column(db.String(64), index=False, unique=False)
    last_name = db.Column(db.String(64), index=False, unique=False)
    name = db.Column(db.String(128), index=False, unique=False)
    email = db.Column(db.String(64), index=False, unique=False)
    phone = db.Column(db.String(64), index=False, unique=False)

    address = db.Column(db.String(128), index=False, unique=False)
    city = db.Column(db.String(64), index=False, unique=False)
    state = db.Column(db.String(32), index=False, unique=False)
    company_name = db.Column(db.String(64), index=False, unique=False)
    postcode = db.Column(db.String(16), index=False, unique=False)
    location = db.Column(db.String(64), index=False, unique=False)

    tags = db.Column(db.String(256), index=False, unique=False)

    notes = db.Column(db.Text(), index=False, unique=False)
    
    
    def __repr__(self):
        return f'<Customer {self.id}>'
        
    def to_dict(self):
        return {col.name: getattr(self, col.name) for col in self.__table__.columns}
    
    @hybrid_property
    def created_at(self):
        if self._created_at:
            return utc_to_local(self._created_at)
        else:
            return None
            
    @created_at.setter
    def created_at(self, val):
        if val is not None and len(val) > 0:
            try:
                if ' ' in val:
                    # '17/07/2020 21:01'
                     self._created_at = datetime.strptime(val, "%d/%m/%Y %H:%M")
                else:
                    # "2018-10-24T13:10:19+10:00"
                    self._created_at = datetime.strptime(val, "%Y-%m-%dT%H:%M:%S%z")
            except ValueError as e:
                current_app.logger.error(f'customer created_at error ({val}): {e}')
    
    @hybrid_property
    def updated_at(self):
        if self._updated_at:
            return utc_to_local(self._updated_at)
        else:
            return None
    
    @updated_at.setter
    def updated_at(self, val):
        if val is not None and len(val) > 0:
            try:
                if ' ' in val:
                    # '17/07/2020 21:01'
                    self._updated_at = datetime.strptime(val, "%d/%m/%Y %H:%M")
                else:
                    # "2018-10-25T11:06:33+10:00"
                    self._updated_at = datetime.strptime(val, "%Y-%m-%dT%H:%M:%S%z")
            except ValueError as e:
                current_app.logger.error(f'customer updated_at error ({val}): {e}')

def import_customer(c, d):
    c.customer_id = d['id'] if 'id' in d else None
    c.created_at = d['created_at'] if 'created_at' in d else None
    c.updated_at = d['updated_at'] if 'updated_at' in d else None
    c.title = d['title'] if 'title' in d else None
    c.first_name = d['first_name'] if 'first_name' in d else None
    c.last_name = d['last_name'] if 'last_name' in d else None
    c.name = d['name'] if 'name' in d else None
    c.email = d['email'] if 'email' in d else None
    c.phone = d['phone'] if 'phone' in d else None
    c.address = d['address'][:128] if 'address' in d else None
    c.city = d['city'] if 'city' in d else None
    c.state = d['state'] if 'state' in d else None
    c.company_name = d['company_name'] if 'company_name' in d else None
    c.postcode = check_postcode(d, "customer_id", d['id']) if 'id' in d else None
    if c.postcode:
        c.location = d['location'] if 'location' in d else None
    c.notes = d['notes'] if 'notes' in d else None
    # Have struck and example of the tags field being filled with the full comments field (?????)
    # I will truncated this to 64 characters, log an error message and send an email to the developer
    #   warning of what I have done.
    if 'tags' in d:
        if len(d['tags']) > 256:
            msg = f'tags data is way too long, exceeds 256 characters. Truncating tag data for {c.name} data={d["tags"]}'
            current_app.logger.warning(msg)
        c.tags = d['tags'][:256] if 'tags' in d else None

    c.profile_url = d['profile_url'] if 'profile_url' in d else None


if __name__ == '__main__':
    def teams_assigned_test(val):
        # "team_details": "[{u'phone': u'+6 (142) 695-8397', u'first_name': u'Irene & Yong',
        # u'last_name': u'', u'image_url': u'', u'name': u'Irene & Yong', u'title': u'Team Euclid',
        #  u'id': u'8447'}]", 
        if val is not None:
            print(val)
            if isinstance(val, str):
                team_list_dict = json.loads(val.replace("'", '"').replace('u"', '"'))
                team_list = [item['title'] for item in team_list_dict]
                print(f'json_str: {team_list}')
            else:
                print(f'funny: {val}')
                if val and  (val[0] != '['):    # Hack for reading CSV file
                    team_list = [ val ]
                else:
                    team_list = []
            print(f'team_list: {team_list}')
            return ','.join(team_list)
    
    val = "[{u'phone': u'+6 (142) 695-8397', u'first_name': u'Irene & Yong', u'last_name': u'', u'image_url': u'', u'name': u'Irene & Yong', u'title': u'Team Euclid', u'id': u'8447'}]"
    res = teams_assigned_test(val)
    print(res)