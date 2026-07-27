"""Structured logging with recursive sensitive-field redaction."""

import logging
from collections.abc import Mapping
from typing import Any, cast

from pythonjsonlogger.json import JsonFormatter

SENSITIVE_KEYS = frozenset(
    {
        "account_number",
        "authorization",
        "card_number",
        "cvv",
        "database_url",
        "password",
        "pin",
        "secret",
        "token",
    }
)
REDACTED = "[REDACTED]"


def redact(value: Any, *, key: str | None = None) -> Any:
    """Recursively redact values whose field names are sensitive."""
    if key is not None and key.casefold() in SENSITIVE_KEYS:
        return REDACTED
    if isinstance(value, Mapping):
        mapping = cast(Mapping[object, object], value)
        return {
            str(item_key): redact(item_value, key=str(item_key))
            for item_key, item_value in mapping.items()
        }
    if isinstance(value, tuple):
        items = cast(tuple[object, ...], value)
        return tuple(redact(item) for item in items)
    if isinstance(value, list):
        items = cast(list[object], value)
        return [redact(item) for item in items]
    return value


class RedactingFilter(logging.Filter):
    """Sanitize structured extras before formatting."""

    def filter(self, record: logging.LogRecord) -> bool:
        for key, value in tuple(record.__dict__.items()):
            record.__dict__[key] = redact(value, key=key)
        return True


def configure_logging(level: str = "INFO") -> None:
    """Configure the root logger once for JSON output."""
    handler = logging.StreamHandler()
    handler.addFilter(RedactingFilter())
    handler.setFormatter(JsonFormatter("%(asctime)s %(levelname)s %(name)s %(message)s"))

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)
