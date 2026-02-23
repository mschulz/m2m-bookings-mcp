# app/models/base.py

import ast
import re
import logging
from datetime import datetime, date

import dateutil.parser
from sqlalchemy import Column, Integer, String, Text, Boolean, Date, DateTime
from sqlalchemy.ext.hybrid import hybrid_property

from app.database import Base
from app.utils.validation import (
    string_to_boolean,
    dollar_string_to_int,
    check_postcode,
    truncate_field,
)
from config import get_settings

logger = logging.getLogger(__name__)


class BookingBase(Base):
    """
    BookingBase is the template for bookings, reservations, and sales_reservations.
    """

    __abstract__ = True

    booking_id = Column(Integer, index=True, unique=True)

    _created_at = Column(DateTime(timezone=True))
    _updated_at = Column(DateTime(timezone=True))
    service_time = Column(String(64))
    _service_date = Column(Date)
    _final_price = Column(Integer)
    _extras_price = Column(Integer)
    _subtotal = Column(Integer)
    _tip = Column(Integer)
    duration = Column(String(32))

    payment_method = Column(String(64))
    _rating_value = Column(Integer)
    rating_text = Column(Text())
    rating_comment = Column(Text())
    _rating_comment_presence = Column(Boolean)
    rating_created_by = Column(String(64))
    rating_received = Column(DateTime(timezone=True))
    rating_modified = Column(DateTime(timezone=True))
    rating_modified_by = Column(String(64))

    frequency = Column(String(64))
    discount_code = Column(String(64))
    _discount_from_code = Column(Integer)
    _giftcard_amount = Column(Integer)
    _teams_assigned = Column(String(80))
    _teams_assigned_ids = Column(String(80))
    _team_share = Column(Integer)
    team_share_summary = Column(String(128))
    team_has_key = Column(String(64))
    team_requested = Column(String(80))
    created_by = Column(String(64))
    _next_booking_date = Column(DateTime(timezone=True))
    service_category = Column(String(64))
    service = Column(String(128))
    customer_notes = Column(Text())
    staff_notes = Column(Text())
    _customer_id = Column(Integer)

    cancellation_type = Column(String(64))
    cancelled_by = Column(String(64))
    _cancellation_date = Column(Date, nullable=True)
    cancellation_reason = Column(Text())
    _cancellation_fee = Column(Integer)
    _cancellation_datetime = Column(DateTime(timezone=True))

    _price_adjustment = Column(Integer)
    price_adjustment_comment = Column(Text())
    booking_status = Column(String(64))
    _is_first_recurring = Column(Boolean)
    _is_new_customer = Column(Boolean)
    was_first_recurring = Column(Boolean, default=False)
    was_new_customer = Column(Boolean, default=False)
    extras = Column(Text())
    source = Column(String(64))
    _sms_notifications_enabled = Column(Boolean)
    pricing_parameters = Column(String(64))
    _pricing_parameters_price = Column(Integer)

    # Customer data
    address = Column(String(128))
    last_name = Column(String(64))
    city = Column(String(64))
    state = Column(String(32))
    first_name = Column(String(64))
    company_name = Column(String(64))
    email = Column(String(64))
    name = Column(String(128))
    phone = Column(String(64))
    postcode = Column(String(16))
    location = Column(String(64))

    # Custom field data
    lead_source = Column(String(64))
    booked_by = Column(String(64))
    _invoice_tobe_emailed = Column(Boolean)
    invoice_name = Column(String(128))
    NDIS_who_pays = Column(String(64))
    invoice_email = Column(String(64))
    last_service = Column(String(80))
    invoice_reference = Column(String(80))
    invoice_reference_extra = Column(String(80))
    NDIS_reference = Column(String(64))
    flexible_date_time = Column(String(64))
    hourly_notes = Column(Text())

    def __repr__(self):
        return f"<Booking {self.id}>"

    def to_dict(self):
        return {col.name: getattr(self, col.name) for col in self.__table__.columns}

    def to_json(self):
        def json_serial(obj):
            if isinstance(obj, (datetime, date)):
                return obj.isoformat()
            return obj

        d = self.to_dict()
        return {k: json_serial(v) for k, v in d.items()}

    @hybrid_property
    def created_at(self):
        return self._created_at

    @staticmethod
    def _unmangle_datetime(val):
        try:
            if "Z" in val:
                return dateutil.parser.isoparse(val)
            elif "am" in val or "pm" in val:
                return datetime.strptime(val, "%d/%m/%Y %I:%M%p")
            elif "T" in val:
                return datetime.strptime(val, "%Y-%m-%dT%H:%M:%S%z")
            elif " " in val:
                return datetime.strptime(val, "%d/%m/%Y %H:%M")
            elif "/" in val:
                return datetime.strptime(val, "%d/%m/%Y")
            else:
                return datetime.strptime(val, "%Y-%m-%d")
        except ValueError as e:
            logger.error("datetime parse error (%s): %s", val, e)
            return ""

    @created_at.setter
    def created_at(self, val):
        if val is not None:
            try:
                self._created_at = self._unmangle_datetime(val)
            except ValueError as e:
                logger.error("created_at error (%s): %s", val, e)

    @hybrid_property
    def updated_at(self):
        return self._updated_at

    @updated_at.setter
    def updated_at(self, val):
        if val is not None:
            try:
                self._updated_at = self._unmangle_datetime(val)
            except ValueError as e:
                logger.error("updated_at error (%s): %s", val, e)

    @hybrid_property
    def service_date(self):
        return self._service_date

    @service_date.setter
    def service_date(self, val):
        if val is not None:
            try:
                if "/" in val:
                    self._service_date = datetime.strptime(val, "%d/%m/%Y")
                else:
                    self._service_date = datetime.strptime(val, "%Y-%m-%d")
            except ValueError as e:
                logger.error("service_date error (%s): %s", val, e)

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
            self._extras_price = dollar_string_to_int(val)

    @hybrid_property
    def subtotal(self):
        return self._subtotal

    @subtotal.setter
    def subtotal(self, val):
        if val is not None:
            self._subtotal = dollar_string_to_int(val)

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
        def fix_single_quotes(json_like_str):
            fixed_str = re.sub(r"(?<!\w)'(.*?)'(?!\w)", r'"\1"', json_like_str)
            return fixed_str

        if val:
            try:
                json_val = ast.literal_eval(val)
            except Exception:
                try:
                    fixed_json = fix_single_quotes(val)
                    json_val = ast.literal_eval(fixed_json)
                except SyntaxError as e:
                    logger.error("Failed to parse team_details: %s", e)
                    raise ValueError("Failed to sanitize input string") from e
            team_details_list = [item[key_str] for item in json_val]
            return ",".join(team_details_list)
        else:
            return ""

    @teams_assigned.setter
    def teams_assigned(self, val):
        if val is not None:
            self._teams_assigned = self.get_team_list(val, "title")

    @hybrid_property
    def teams_assigned_ids(self):
        return self._teams_assigned_ids

    @teams_assigned_ids.setter
    def teams_assigned_ids(self, val):
        if val is not None:
            self._teams_assigned_ids = self.get_team_list(val, "id")

    @hybrid_property
    def team_share(self):
        return self._team_share

    @team_share.setter
    def team_share(self, val):
        if val and "," not in val:
            try:
                if "-" in val:
                    self._team_share = dollar_string_to_int(val.split(" - ")[-1])
                else:
                    self._team_share = dollar_string_to_int(val)
            except (IndexError, ValueError) as e:
                logger.error("team share error (%s): %s", val, e)

    @hybrid_property
    def next_booking_date(self):
        return self._next_booking_date

    @next_booking_date.setter
    def next_booking_date(self, val):
        if val is not None and len(val) > 0:
            try:
                self._next_booking_date = self._unmangle_datetime(val)
            except ValueError as e:
                logger.error("next_booking_date error (%s): %s", val, e)

    @hybrid_property
    def customer_id(self):
        return self._customer_id

    @customer_id.setter
    def customer_id(self, val):
        if val is not None:
            self._customer_id = int(val)

    @hybrid_property
    def cancellation_date(self):
        return self._cancellation_date

    @cancellation_date.setter
    def cancellation_date(self, val):
        if val:
            try:
                self._cancellation_date = self._unmangle_datetime(val).date()
            except (ValueError, AttributeError) as e:
                logger.error("cancellation_date error (%s): %s", val, e)

    @hybrid_property
    def cancellation_fee(self):
        return self._cancellation_fee

    @cancellation_fee.setter
    def cancellation_fee(self, val):
        if not isinstance(val, str):
            val = str(val)
        if val is not None and len(val) > 0:
            self._cancellation_fee = dollar_string_to_int(val)

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
                logger.error("price_adjustment error (%s): %s", val, e)

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
            self._sms_notifications_enabled = string_to_boolean(val)

    @hybrid_property
    def pricing_parameters_price(self):
        return self._pricing_parameters_price

    @pricing_parameters_price.setter
    def pricing_parameters_price(self, val):
        if not isinstance(val, str):
            val = str(val)
        if val is not None and len(val) > 0:
            try:
                self._pricing_parameters_price = dollar_string_to_int(val)
            except ValueError as e:
                logger.error("pricing_parameters_price error (%s): %s", val, e)

    @staticmethod
    def import_dict(d, b):
        settings = get_settings()
        bid = b.get("id")

        if "id" in b:
            d.booking_id = b["id"]
        d.created_at = b.get("created_at")
        d.updated_at = b.get("updated_at")
        d.service_time = truncate_field(b.get("service_time"), 64, "service_time", bid)
        d.service_date = b.get("service_date")
        d.duration = truncate_field(b.get("duration"), 32, "duration", bid)
        d.final_price = b.get("final_price")
        d.extras_price = b.get("extras_price")
        d.subtotal = b.get("subtotal")
        d.tip = b.get("tip")
        d.payment_method = truncate_field(b.get("payment_method"), 64, "payment_method", bid)
        d.frequency = truncate_field(b.get("frequency"), 64, "frequency", bid)
        if "discount_code" in b:
            d.discount_code = truncate_field(b["discount_code"], 64, "discount_code", bid)
        d.discount_from_code = b.get("discount_amount")
        d.giftcard_amount = b.get("giftcard_amount")
        if "team_details" in b:
            d.teams_assigned = b["team_details"]
            d.teams_assigned_ids = b["team_details"]
        if "team_share_amount" in b:
            d.team_share = b["team_share_amount"]
        if "team_share_total" in b:
            d.team_share_summary = truncate_field(b["team_share_total"], 128, "team_share_summary", bid)
        d.team_has_key = truncate_field(b.get("team_has_key"), 64, "team_has_key", bid)
        d.team_requested = truncate_field(b.get("team_requested"), 80, "team_requested", bid)
        d.created_by = truncate_field(b.get("created_by"), 64, "created_by", bid)
        if "next_booking_date" in b:
            d.next_booking_date = b["next_booking_date"]
        d.service_category = truncate_field(
            b.get("service_category", settings.SERVICE_CATEGORY_DEFAULT),
            64, "service_category", bid,
        )
        if "service" in b:
            d.service = truncate_field(b["service"], 128, "service", bid)
        d.customer_notes = b.get("customer_notes")
        d.staff_notes = b.get("staff_notes")
        d.customer_id = b.get("customer", {}).get("id")
        d.cancellation_type = truncate_field(b.get("cancellation_type"), 64, "cancellation_type", bid)
        d.cancelled_by = truncate_field(b.get("cancelled_by"), 64, "cancelled_by", bid)
        d.cancellation_date = b.get("cancellation_date")
        d._cancellation_datetime = b.get("_cancellation_datetime")
        d.cancellation_reason = b.get("cancellation_reason")
        d.cancellation_fee = b.get("cancellation_fee")
        d.price_adjustment = b.get("price_adjustment")
        d.price_adjustment_comment = b.get("price_adjustment_comment")
        d.booking_status = truncate_field(b.get("booking_status"), 64, "booking_status", bid)
        d.is_first_recurring = b.get("is_first_recurring")
        if d.is_first_recurring:
            d.was_first_recurring = True
        d.is_new_customer = b.get("is_new_customer")
        if d.is_new_customer:
            d.was_new_customer = True
        d.extras = b.get("extras")
        d.source = truncate_field(b.get("source"), 64, "source", bid)
        d.state = truncate_field(b.get("state"), 32, "state", bid)
        d.sms_notifications_enabled = b.get("sms_notifications_enabled")
        d.pricing_parameters = truncate_field(b.get("pricing_parameters"), 64, "pricing_parameters", bid)
        if d.pricing_parameters:
            d.pricing_parameters = d.pricing_parameters.replace("<br/>", ", ")
        d.pricing_parameters_price = b.get("pricing_parameters_price")

        # Customer data
        d.address = truncate_field(b.get("address"), 128, "address", bid)
        d.last_name = truncate_field(b.get("last_name"), 64, "last_name", bid)
        d.city = truncate_field(b.get("city"), 64, "city", bid)
        d.first_name = truncate_field(b.get("first_name"), 64, "first_name", bid)
        d.name = truncate_field(b.get("name"), 128, "name", bid)
        d.company_name = truncate_field(b.get("company_name"), 64, "company_name", bid)
        d.email = truncate_field(b.get("email"), 64, "email", bid)
        d.phone = truncate_field(b.get("phone"), 64, "phone", bid)
        d.postcode = check_postcode(b, "booking_id", b.get("id"))
        if d.postcode:
            from app.services.locations import get_location
            d.location = truncate_field(
                b.get("location", get_location(d.postcode)),
                64, "location", bid,
            )

        # Custom field data
        if "custom_fields" in b:
            process_custom_fields(d, b["custom_fields"], bid)


def process_custom_fields(d, b_cf, record_id=None):
    settings = get_settings()

    if settings.CUSTOM_SOURCE and settings.CUSTOM_SOURCE in b_cf:
        d.lead_source = truncate_field(b_cf[settings.CUSTOM_SOURCE], 64, "lead_source", record_id)

    if settings.CUSTOM_BOOKED_BY and settings.CUSTOM_BOOKED_BY in b_cf:
        d.booked_by = truncate_field(b_cf[settings.CUSTOM_BOOKED_BY], 64, "booked_by", record_id)

    if settings.CUSTOM_EMAIL_INVOICE and settings.CUSTOM_EMAIL_INVOICE in b_cf:
        d.invoice_tobe_emailed = b_cf.get(settings.CUSTOM_EMAIL_INVOICE)

    if settings.CUSTOM_INVOICE_NAME and settings.CUSTOM_INVOICE_NAME in b_cf:
        d.invoice_name = truncate_field(b_cf.get(settings.CUSTOM_INVOICE_NAME), 128, "invoice_name", record_id)

    if settings.CUSTOM_WHO_PAYS and settings.CUSTOM_WHO_PAYS in b_cf:
        d.NDIS_who_pays = truncate_field(b_cf.get(settings.CUSTOM_WHO_PAYS), 64, "NDIS_who_pays", record_id)

    if settings.CUSTOM_INVOICE_EMAIL_ADDRESS and settings.CUSTOM_INVOICE_EMAIL_ADDRESS in b_cf:
        d.invoice_email = truncate_field(b_cf[settings.CUSTOM_INVOICE_EMAIL_ADDRESS], 64, "invoice_email", record_id)

    if settings.CUSTOM_LAST_SERVICE and settings.CUSTOM_LAST_SERVICE in b_cf:
        d.last_service = truncate_field(b_cf.get(settings.CUSTOM_LAST_SERVICE), 80, "last_service", record_id)

    if settings.CUSTOM_INVOICE_REFERENCE and settings.CUSTOM_INVOICE_REFERENCE in b_cf:
        d.invoice_reference = truncate_field(b_cf.get(settings.CUSTOM_INVOICE_REFERENCE), 80, "invoice_reference", record_id)

    if settings.CUSTOM_INVOICE_REFERENCE_EXTRA and settings.CUSTOM_INVOICE_REFERENCE_EXTRA in b_cf:
        d.invoice_reference_extra = truncate_field(b_cf.get(settings.CUSTOM_INVOICE_REFERENCE_EXTRA), 80, "invoice_reference_extra", record_id)

    if settings.CUSTOM_NDIS_NUMBER and settings.CUSTOM_NDIS_NUMBER in b_cf:
        d.NDIS_reference = truncate_field(b_cf.get(settings.CUSTOM_NDIS_NUMBER), 64, "NDIS_reference", record_id)

    if settings.CUSTOM_FLEXIBLE and settings.CUSTOM_FLEXIBLE in b_cf:
        d.flexible_date_time = truncate_field(b_cf.get(settings.CUSTOM_FLEXIBLE), 64, "flexible_date_time", record_id)

    if settings.CUSTOM_HOURLY_NOTES and settings.CUSTOM_HOURLY_NOTES in b_cf:
        d.hourly_notes = b_cf.get(settings.CUSTOM_HOURLY_NOTES)

    return d
