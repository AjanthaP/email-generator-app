"""Logging setup: one JSON object per line on stdout, or plain text.

Cloud Run forwards stdout to Cloud Logging, which turns each JSON line into a
structured entry: ``severity`` and ``message`` become the entry's severity and
summary, and the other keys land in ``jsonPayload``. Every line also carries
the current ``request_id`` and ``agent`` so a request can be traced across
agents.

Set ``LOG_FORMAT=text`` for human-readable local logs.
"""
from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone

from . import telemetry

_MARKER = "_email_app_handler"


class ContextFilter(logging.Filter):
    """Attach the current request ID and agent to every log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        if not getattr(record, "request_id", None):
            record.request_id = telemetry.current_request_id() or "-"
        if not getattr(record, "agent", None):
            record.agent = telemetry.current_agent() or "-"
        return True


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "severity": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "time": datetime.fromtimestamp(record.created, timezone.utc)
            .isoformat(timespec="milliseconds")
            .replace("+00:00", "Z"),
        }
        for key in ("request_id", "agent"):
            value = getattr(record, key, None)
            if value and value != "-":
                payload[key] = value
        fields = getattr(record, "json_fields", None)
        if isinstance(fields, dict):
            for key, value in fields.items():
                payload.setdefault(key, value)
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        if record.stack_info:
            payload["stack"] = self.formatStack(record.stack_info)
        return json.dumps(payload, default=str, ensure_ascii=False)


TEXT_FORMAT = "%(asctime)s %(levelname)s %(name)s [%(request_id)s %(agent)s] %(message)s"


def configure_logging(level: str = "INFO", fmt: str = "json") -> None:
    """Send all logs (app, uvicorn, telemetry) to stdout in one format."""
    root = logging.getLogger()
    for handler in list(root.handlers):
        if getattr(handler, _MARKER, False):
            root.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    setattr(handler, _MARKER, True)
    handler.addFilter(ContextFilter())
    if str(fmt).lower() == "text":
        handler.setFormatter(logging.Formatter(TEXT_FORMAT))
    else:
        handler.setFormatter(JsonFormatter())
    root.addHandler(handler)
    root.setLevel(getattr(logging, str(level).upper(), logging.INFO))

    # uvicorn installs its own text handlers; route its logs through ours.
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        uv_logger = logging.getLogger(name)
        uv_logger.handlers.clear()
        uv_logger.propagate = True

    # Telemetry events are INFO; keep them even when LOG_LEVEL is WARNING.
    logging.getLogger("telemetry").setLevel(logging.INFO)


__all__ = ["configure_logging", "JsonFormatter", "ContextFilter", "TEXT_FORMAT"]
