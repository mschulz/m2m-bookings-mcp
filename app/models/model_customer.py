# app/models/model_customer.py

from datetime import datetime, date

from app import db
from sqlalchemy.ext.hybrid import hybrid_property

from flask import current_app
from app.locations import get_location
from app.models.model_base import check_postcode
from app.local_date_time import utc_to_local


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


    @staticmethod
    def import_customer(c, d):
        c.customer_id = d.get('id')
        c.created_at = d.get('created_at')
        c.updated_at = d.get('updated_at')
        c.title = d.get('title')
        c.first_name = d.get('first_name')
        c.last_name = d.get('last_name')
        c.name = d.get('name')
        c.email = d.get('email')
        c.phone = d.get('phone')
        c.address = d.get('address')
        c.city = d.get('city')
        c.state = d.get('state')
        c.company_name = d.get('company_name')
        c.postcode = check_postcode(d, "customer_id", d.get('id'))
        if c.postcode:
            c.location = d.get('location', get_location(c.postcode))
        c.notes = d.get('notes')
        # Have struck and example of the tags field being filled with the full comments field (?????)
        # I will truncated this to 64 characters, log an error message and send an email to the developer
        #   warning of what I have done.
        if 'tags' in d:
            if len(d['tags']) > 256:
                msg = f'tags data is way too long, exceeds 256 characters. Truncating tag data for {c.name} data={d["tags"]}'
                current_app.logger.warning(msg)
            c.tags = d['tags'][:256] if 'tags' in d else None

        c.profile_url = d.get('profile_url')

