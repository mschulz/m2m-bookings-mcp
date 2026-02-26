"""Customer model with webhook import logic."""

import logging

from sqlalchemy import Text, DateTime
from sqlmodel import SQLModel, Field

from app.utils.validation import (
    check_postcode,
    truncate_field,
    parse_datetime,
    safe_int,
)

logger = logging.getLogger(__name__)


class Customer(SQLModel, table=True):
    __tablename__ = "customer"

    id: int | None = Field(default=None, primary_key=True)

    customer_id: int | None = Field(default=None, index=True)
    created_at: str | None = Field(default=None, sa_type=DateTime(timezone=True), sa_column_kwargs={"name": "_created_at"})
    updated_at: str | None = Field(default=None, sa_type=DateTime(timezone=True), sa_column_kwargs={"name": "_updated_at"})

    # Customer data
    title: str | None = Field(default=None, max_length=16)
    first_name: str | None = Field(default=None, max_length=64)
    last_name: str | None = Field(default=None, max_length=64)
    name: str | None = Field(default=None, max_length=128)
    email: str | None = Field(default=None, max_length=64)
    phone: str | None = Field(default=None, max_length=64)

    address: str | None = Field(default=None, max_length=128)
    city: str | None = Field(default=None, max_length=64)
    state: str | None = Field(default=None, max_length=32)
    company_name: str | None = Field(default=None, max_length=64)
    postcode: str | None = Field(default=None, max_length=16)
    location: str | None = Field(default=None, max_length=64)

    tags: str | None = Field(default=None, max_length=256)
    notes: str | None = Field(default=None, sa_type=Text)

    def __repr__(self):
        return f"<Customer {self.id}>"

    @classmethod
    def from_webhook(cls, data: dict):
        """Create a new Customer from webhook data dict."""
        instance = cls()
        _apply_customer_data(instance, data)
        return instance

    def update_from_webhook(self, data: dict):
        """Update this Customer from webhook data dict."""
        _apply_customer_data(self, data)


def _apply_customer_data(c, d: dict) -> None:
    """Apply webhook dict to a Customer instance with explicit coercion."""
    cid = d.get("id")
    c.customer_id = safe_int(d.get("id"))
    c.created_at = parse_datetime(d.get("created_at"))
    c.updated_at = parse_datetime(d.get("updated_at"))
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
    if d.get("location"):
        c.location = truncate_field(d["location"], 64, "location", cid)
    c.notes = d.get("notes")
    if "tags" in d:
        c.tags = truncate_field(d.get("tags"), 256, "tags", cid)
