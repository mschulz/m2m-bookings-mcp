# /app/database/model.py

"""
	A run-once program to calculate historical data and store in a table in the database.
		date, today gain, today loss, today nett, recurring count
"""

from app import db


class History(db.Model):
    __tablename__ = 'history'
    
    id = db.Column(db.Integer, primary_key=True)
    
    day_date = db.Column(db.Date, index=False, unique=False)
    gain = db.Column(db.Integer, index=False, unique=False)
    loss = db.Column(db.Integer, index=False, unique=False)
    nett = db.Column(db.Integer, index=False, unique=False)
    recurring = db.Column(db.Integer, index=False, unique=False)
    
    def __repr__(self):
        return f'<History {day_date} {nett} {recurring}>'

