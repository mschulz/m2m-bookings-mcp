"""Field validation and coercion helpers for booking and customer data."""

import logging
from typing import Any

logger = logging.getLogger(__name__)


def truncate_field(
    value: str | None, max_length: int, field_name: str, record_id: Any = None
) -> str | None:
    """Truncate string to max_length, logging a warning if truncation occurs."""
    if value is None:
        return None
    if len(value) > max_length:
        logger.warning(
            "Field '%s' truncated from %d to %d chars (record: %s)",
            field_name, len(value), max_length, record_id,
        )
        return value[:max_length]
    return value


def string_to_boolean(val) -> bool:
    """Convert a string like 'true', 'yes', or '1' to a boolean."""
    if isinstance(val, bool):
        return val
    return val.lower() in ["true", "yes", "1"]


def dollar_string_to_int(val) -> int:
    """Convert a dollar string like '$67.64' to an integer in cents (6764)."""
    if val is None or val == "None":
        return 0
    if isinstance(val, str):
        return int(val.replace("$", "").replace(".", ""))
    return int(str(val).replace("$", "").replace(".", ""))


def check_postcode(data: dict, who: str, who_id: Any) -> str | None:
    """Validate postcode is numeric. Returns postcode string or None."""
    p = data.get("zip", None)
    if p:
        if p.isnumeric():
            return p
        which_id = data.get("booking_id", who_id)
        logger.error(
            "Invalid postcode %s NOT entered for %s '%s'", p, who, which_id
        )
    return None
