"""Field validation and coercion helpers for booking and customer data."""

import ast
import re
import logging
from datetime import datetime, date
from typing import Any

import dateutil.parser

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


def parse_datetime(val: str | None) -> datetime | None:
    """Parse a datetime string in any of the expected inbound formats."""
    if val is None or (isinstance(val, str) and len(val) == 0):
        return None
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
    except (ValueError, TypeError) as e:
        logger.error("datetime parse error (%s): %s", val, e)
        return None


def parse_date(val: str | None) -> date | None:
    """Parse a date string, extracting just the date portion."""
    if val is None or (isinstance(val, str) and len(val) == 0):
        return None
    try:
        if "/" in val and "T" not in val and " " not in val:
            return datetime.strptime(val, "%d/%m/%Y").date()
        elif "T" not in val and " " not in val and "/" not in val:
            return datetime.strptime(val, "%Y-%m-%d").date()
        else:
            # Fallback: parse as datetime and extract date
            dt = parse_datetime(val)
            return dt.date() if dt else None
    except (ValueError, TypeError, AttributeError) as e:
        logger.error("date parse error (%s): %s", val, e)
        return None


def parse_team_list(val: str | None, key: str) -> str:
    """Extract a comma-separated string of values from a stringified list of dicts."""
    def fix_single_quotes(json_like_str):
        return re.sub(r"(?<!\w)'(.*?)'(?!\w)", r'"\1"', json_like_str)

    if not val:
        return ""
    try:
        json_val = ast.literal_eval(val)
    except Exception:
        try:
            fixed_json = fix_single_quotes(val)
            json_val = ast.literal_eval(fixed_json)
        except SyntaxError as e:
            logger.error("Failed to parse team_details: %s", e)
            raise ValueError("Failed to sanitize input string") from e
    team_details_list = [str(item[key]) for item in json_val]
    return ",".join(team_details_list)


def parse_team_share(val: str | None) -> int | None:
    """Parse team share string like 'Name - $XX.XX' into cents."""
    if not val or "," in val:
        return None
    try:
        if "-" in val:
            return dollar_string_to_int(val.split(" - ")[-1])
        else:
            return dollar_string_to_int(val)
    except (IndexError, ValueError) as e:
        logger.error("team share error (%s): %s", val, e)
        return None


def safe_int(val) -> int | None:
    """Convert string/empty to int, returning None for empty or None values."""
    if val is None:
        return None
    if isinstance(val, int):
        return val
    if isinstance(val, str):
        if len(val) == 0:
            return None
        return int(val)
    return int(val)


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
