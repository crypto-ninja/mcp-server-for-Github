"""Type helper utilities for normalizing API responses and type conversions."""

import json
from typing import Any, Dict, List


def ensure_dict(x: Any) -> Dict[str, Any]:
    """
    Ensure a value is a dict, converting from JSON string if needed.

    Args:
        x: Value that should be a dict (dict, JSON string, or other)

    Returns:
        Dict[str, Any]

    Raises:
        TypeError: If value cannot be converted to dict
    """
    if isinstance(x, dict):
        return x
    if isinstance(x, str):
        try:
            parsed = json.loads(x)
            if isinstance(parsed, dict):
                return parsed
            raise TypeError(f"JSON string parsed to {type(parsed)}, expected dict")
        except json.JSONDecodeError as e:
            raise TypeError(f"Invalid JSON string: {e}") from e
    raise TypeError(f"Expected dict or JSON string, got {type(x)}")


def ensure_list(x: Any) -> List[Any]:
    """
    Ensure a value is a list, converting from single value or None if needed.

    Args:
        x: Value that should be a list (list, single value, or None)

    Returns:
        List[Any]
    """
    if x is None:
        return []
    if isinstance(x, list):
        return x
    return [x]


def ensure_list_str(x: Any) -> List[str]:
    """
    Ensure a value is a list of strings, normalizing from various formats.

    Args:
        x: Value that should be a list of strings (list, single str, None, etc.)

    Returns:
        List[str]
    """
    if x is None:
        return []
    if isinstance(x, list):
        return [str(i) for i in x]
    return [str(x)]


def ensure_int_or_default(x: Any, default: int = 0) -> int:
    """
    Ensure a value is an int, using default if None or invalid.

    Args:
        x: Value that should be an int (int, None, or convertible)
        default: Default value if x is None or invalid

    Returns:
        int
    """
    if x is None:
        return default
    if isinstance(x, int):
        return x
    try:
        return int(x)
    except (ValueError, TypeError):
        return default


def ensure_str_or_default(x: Any, default: str = "") -> str:
    """
    Ensure a value is a string, using default if None.

    Args:
        x: Value that should be a string (str, None, or convertible)
        default: Default value if x is None

    Returns:
        str
    """
    if x is None:
        return default
    if isinstance(x, str):
        return x
    return str(x)
