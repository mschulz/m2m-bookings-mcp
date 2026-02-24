"""Customer model with import logic for webhook customer data."""

import logging
from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.ext.hybrid import hybrid_property

from app.database import Base
from app.utils.validation import check_postcode, truncate_field

logger = logging.getLogger(__name__)


class Customer(Base):
    __tablename__ = "customer"

    id = Column(Integer, primary_key=True)

    customer_id = Column(Integer, index=True, unique=False)
    _created_at = Column(DateTime(timezone=True))
    _updated_at = Column(DateTime(timezone=True))

    # Customer data
    title = Column(String(16))
    first_name = Column(String(64))
    last_name = Column(String(64))
    name = Column(String(128))
    email = Column(String(64))
    phone = Column(String(64))

    address = Column(String(128))
    city = Column(String(64))
    state = Column(String(32))
    company_name = Column(String(64))
    postcode = Column(String(16))
    location = Column(String(64))

    tags = Column(String(256))
    notes = Column(Text())

    def __repr__(self):
        return f"<Customer {self.id}>"

    def to_dict(self):
        """Return all column values as a dictionary."""
        return {col.name: getattr(self, col.name) for col in self.__table__.columns}

    @hybrid_property
    def created_at(self):
        return self._created_at

    @created_at.setter
    def created_at(self, val):
        if val is not None and len(val) > 0:
            try:
                if " " in val:
                    self._created_at = datetime.strptime(val, "%d/%m/%Y %H:%M")
                else:
                    self._created_at = datetime.strptime(val, "%Y-%m-%dT%H:%M:%S%z")
            except ValueError as e:
                logger.error("customer created_at error (%s): %s", val, e)

    @hybrid_property
    def updated_at(self):
        return self._updated_at

    @updated_at.setter
    def updated_at(self, val):
        if val is not None and len(val) > 0:
            try:
                if " " in val:
                    self._updated_at = datetime.strptime(val, "%d/%m/%Y %H:%M")
                else:
                    self._updated_at = datetime.strptime(val, "%Y-%m-%dT%H:%M:%S%z")
            except ValueError as e:
                logger.error("customer updated_at error (%s): %s", val, e)

    @staticmethod
    def import_customer(c, d):
        """Populate customer instance *c* from webhook data dict *d*."""
        cid = d.get("id")
        c.customer_id = d.get("id")
        c.created_at = d.get("created_at")
        c.updated_at = d.get("updated_at")
        c.title = truncate_field(d.get("title"), 16, "title", cid)
        c.first_name = truncate_field(d.get("first_name"), 64, "first_name", cid)
        c.last_name = truncate_field(d.get("last_name"), 64, "last_name", cid)
        c.name = truncate_field(d.get("name"), 128, "name", cid)
        c.email = truncate_field(d.get("email"), 64, "email", cid)
        c.phone = truncate_field(d.get("phone"), 64, "phone", cid)
        c.address = truncate_field(d.get("address"), 128, "address", cid)
        c.city = truncate_field(d.get("city"), 64, "city", cid)
        c.state = truncate_field(d.get("state"), 32, "state", cid)
        c.company_name = truncate_field(d.get("company_name"), 64, "company_name", cid)
        c.postcode = check_postcode(d, "customer_id", d.get("id"))
        if c.postcode:
            from app.utils.locations import get_location
            c.location = truncate_field(
                d.get("location", get_location(c.postcode)),
                64, "location", cid,
            )
        c.notes = d.get("notes")
        if "tags" in d:
            if d["tags"] and len(d["tags"]) > 256:
                logger.warning(
                    "tags data exceeds 256 chars, truncating for %s", c.name,
                )
            c.tags = truncate_field(d.get("tags"), 256, "tags", cid)
