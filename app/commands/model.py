# app/commands/model.py

"""
A History model for storing historical gain/loss data.
"""

from datetime import datetime

import pendulum as pdl
from sqlalchemy import Column, Integer, Date, Boolean

from app.database import Base


class History(Base):
    __tablename__ = "history"

    id = Column(Integer, primary_key=True)

    day_date = Column(Date)
    gain = Column(Integer)
    loss = Column(Integer)
    nett = Column(Integer)
    recurring = Column(Integer)
    is_saturday = Column(Boolean)
    is_eom = Column(Boolean)

    def __repr__(self):
        return (
            f"<History {self.day_date=} {self.gain=} {self.loss=} "
            f"{self.nett=} {self.recurring=} {self.is_saturday=} {self.is_eom=}>"
        )

    def to_json(self):
        return {
            "day_date": pdl.instance(
                datetime.fromordinal(self.day_date.toordinal())
            ).to_date_string(),
            "gain": self.gain,
            "loss": self.loss,
            "nett": self.nett,
            "recurring": self.recurring,
            "is_saturday": self.is_saturday,
            "is_eom": self.is_eom,
        }
