# /app/database/model.py

"""
	A run-once program to calculate historical data and store in a table in the database.
		date, today gain, today loss, today nett, recurring count
"""

from app import db
from datetime import datetime
import pendulum as pdl


class History(db.Model):
    __tablename__ = 'history'
    
    id = db.Column(db.Integer, primary_key=True)
    
    day_date = db.Column(db.Date, index=False, unique=False)
    gain = db.Column(db.Integer, index=False, unique=False)
    loss = db.Column(db.Integer, index=False, unique=False)
    nett = db.Column(db.Integer, index=False, unique=False)
    recurring = db.Column(db.Integer, index=False, unique=False)
    is_saturday = db.Column(db.Boolean, index=False, unique=False)
    is_eom = db.Column(db.Boolean, index=False, unique=False)
    
    def __repr__(self):
        return f'<History {self.day_date=} {self.gain=} {self.loss=} {self.nett=} {self.recurring=} {self.is_saturday=} {self.is_eom=}>'

    def to_json(self):
        return {
            "day_date": pdl.instance(datetime.fromordinal(self.day_date.toordinal())).to_date_string(),
            "gain": self.gain,
            "loss": self.loss,
            "nett": self.nett,
            "recurring": self.recurring,
            "is_saturday": self.is_saturday,
            "is_eom": self.is_eom
        }