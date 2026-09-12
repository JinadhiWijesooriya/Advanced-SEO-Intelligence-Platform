"""
Centralized Structured Logging Configuration — Phase 10

Provides:
  - Human-readable colored text logs in development (LOG_FORMAT=text)
  - JSON-structured machine-parseable logs in production (LOG_FORMAT=json)
  - Rotating file handler persisting logs to storage/logs/app.log
  - Configurable log level via LOG_LEVEL env var (default: INFO)

Usage:
    from app.core.logging_config import setup_logging
    setup_logging()   # call once at app startup
"""
from __future__ import annotations

import json
import logging
import logging.handlers
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


# ---------------------------------------------------------------------------
# JSON log formatter
# ---------------------------------------------------------------------------

class JSONFormatter(logging.Formatter):
    """Formats log records as single-line JSON objects for log aggregators."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "line": record.lineno,
        }
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        # Include any extra fields attached by middleware (e.g. request_id)
        for key in ("request_id", "method", "path", "status_code", "duration_ms"):
            val = getattr(record, key, None)
            if val is not None:
                log_entry[key] = val
        return json.dumps(log_entry, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Text formatter (development)
# ---------------------------------------------------------------------------

class DevFormatter(logging.Formatter):
    COLORS = {
        "DEBUG": "\033[36m",     # Cyan
        "INFO": "\033[32m",      # Green
        "WARNING": "\033[33m",   # Yellow
        "ERROR": "\033[31m",     # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, "")
        ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
        prefix = f"{color}[{record.levelname[:4]}]{self.RESET}"
        return f"{ts} {prefix} {record.name}: {record.getMessage()}"


# ---------------------------------------------------------------------------
# Setup function
# ---------------------------------------------------------------------------

def setup_logging() -> None:
    """
    Configure the root logger and key application loggers.
    Call this exactly once at application startup.
    """
    from app.core.config import settings

    log_level_str = settings.LOG_LEVEL.upper()
    log_level = getattr(logging, log_level_str, logging.INFO)
    log_format = settings.LOG_FORMAT.lower()

    # Choose formatter
    if log_format == "json":
        formatter: logging.Formatter = JSONFormatter()
    else:
        formatter = DevFormatter()

    # --- Console handler ---
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)

    # --- Rotating file handler ---
    log_dir = Path(os.path.dirname(__file__)).parent.parent.parent / "storage" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "app.log"

    file_handler = logging.handlers.RotatingFileHandler(
        filename=str(log_file),
        maxBytes=10 * 1024 * 1024,   # 10 MB per file
        backupCount=5,
        encoding="utf-8",
    )
    # File logs are always JSON for machine parsing
    file_handler.setFormatter(JSONFormatter())
    file_handler.setLevel(log_level)

    # --- Root logger ---
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    # Clear any existing handlers (avoids duplicate output from uvicorn defaults)
    root_logger.handlers.clear()
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    # Quieten noisy third-party loggers
    for noisy in ("httpx", "httpcore", "celery.worker.strategy", "urllib3"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    logging.getLogger("app").setLevel(log_level)
    logging.getLogger(__name__).info(
        "Logging initialised",
        extra={"log_format": log_format, "log_level": log_level_str},
    )
