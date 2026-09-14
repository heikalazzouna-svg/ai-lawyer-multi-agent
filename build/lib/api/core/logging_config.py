"""
Structured Logging Configuration
=================================
Centralised logging setup using Python's built-in logging with JSON formatting.
Designed for production environments where logs are ingested by ELK / Datadog / CloudWatch.
"""

import logging
import json
import sys
from datetime import datetime, timezone
from typing import Any


class JSONFormatter(logging.Formatter):
    """
    Outputs log records as single-line JSON objects.
    This format is directly ingestible by log aggregation platforms
    (ELK Stack, AWS CloudWatch, Datadog, Grafana Loki).
    """

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Merge any extra fields passed via logger.info(..., extra={...})
        if hasattr(record, "operation"):
            log_entry["operation"] = record.operation
        if hasattr(record, "metadata"):
            log_entry["metadata"] = record.metadata
        if hasattr(record, "latency_seconds"):
            log_entry["latency_seconds"] = record.latency_seconds
        if hasattr(record, "error"):
            log_entry["error"] = record.error

        # Capture exception info if present
        if record.exc_info and record.exc_info[0] is not None:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry, default=str)


def configure_logging(level: str = "INFO") -> None:
    """
    Configure structured JSON logging for the entire application.
    Call this once at FastAPI startup.

    Args:
        level: The minimum log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Remove any existing handlers to avoid duplicate output
    root_logger.handlers.clear()

    # Create a single stdout handler with JSON formatting
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    root_logger.addHandler(handler)

    # Suppress noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    logging.getLogger("ai_lawyer").info("Structured logging initialized", extra={"level": level})
