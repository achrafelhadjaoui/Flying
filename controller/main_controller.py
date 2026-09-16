"""Validation of the data produced by the parser."""

from typing import Any

from pydantic import ValidationError
from pydantic_core import ErrorDetails

from data_validation import ConfigValidator


def describe_error(error: ErrorDetails, data: dict[str, Any]) -> str:
    """Turn one pydantic error into a message naming the guilty line.

    Args:
        error (ErrorDetails): one entry of ValidationError.errors().
        data (dict[str, Any]): the parsed content of the map file.

    Returns:
        str: the message shown to the user.
    """
    location = error["loc"]
    field = str(location[0])
    message = error["msg"]

    # a 'zones' or 'connections' error points at one entry, and every
    # entry remembers the line it was read on
    if len(location) > 1 and field in ("zones", "connections"):
        entries = data.get(field, [])
        position = location[1]

        if isinstance(position, int) and position < len(entries):
            detail = ".".join(str(part) for part in location[2:])

            return (
                f"Line {entries[position]['line']}, "
                f"{detail or field} {message}"
            )

    return f"{field} {message}"


def validate_data(data: dict[str, Any]) -> None:
    """Validate our entered data after parsing it.

    Args:
        data (dict[str, Any]): the parsed content of the map file.
    """
    try:
        ConfigValidator(**data)
    except ValidationError as e:
        errors = [describe_error(error, data) for error in e.errors()]

        raise ValueError("\n".join(errors)) from e
