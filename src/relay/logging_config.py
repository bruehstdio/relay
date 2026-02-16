"""Structured logging configuration for Relay."""

from __future__ import annotations

import json
import logging
import os
import sys
from enum import Enum
from typing import Any


class LogLevel(str, Enum):
    """Log level options."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"


class JsonFormatter(logging.Formatter):
    """JSON log formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data: dict[str, Any] = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in {
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "exc_info",
                "exc_text",
                "stack_info",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
                "getMessage",
                "asctime",
            }:
                log_data[key] = value

        return json.dumps(log_data)


class RelayLogger:
    """Structured logger for Relay operations."""

    _instance: RelayLogger | None = None
    _logger: logging.Logger | None = None
    _json_mode: bool = False

    def __new__(cls) -> RelayLogger:
        """Singleton pattern for RelayLogger."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def setup(
        self,
        level: LogLevel | str = LogLevel.INFO,
        json_format: bool = False,
    ) -> None:
        """Setup the logger configuration.

        Args:
            level: Minimum log level to display
            json_format: Whether to output logs in JSON format
        """
        self._json_mode = json_format
        self._logger = logging.getLogger("relay")
        self._logger.setLevel(self._parse_level(level))

        # Clear existing handlers
        self._logger.handlers = []

        # Create console handler
        handler = logging.StreamHandler(sys.stderr)
        handler.setLevel(self._parse_level(level))

        # Set formatter based on mode
        formatter: logging.Formatter
        if json_format:
            formatter = JsonFormatter()
        else:
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )

        handler.setFormatter(formatter)
        self._logger.addHandler(handler)

    def _parse_level(self, level: LogLevel | str) -> int:
        """Parse log level string to logging constant."""
        level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARN": logging.WARNING,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
        }
        level_str = str(level).upper()
        return level_map.get(level_str, logging.INFO)

    @property
    def logger(self) -> logging.Logger:
        """Get the configured logger."""
        if self._logger is None:
            self.setup()
        return self._logger  # type: ignore

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message."""
        self._log(logging.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message."""
        self._log(logging.INFO, message, **kwargs)

    def warn(self, message: str, **kwargs: Any) -> None:
        """Log warning message."""
        self._log(logging.WARNING, message, **kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message (alias for warn)."""
        self._log(logging.WARNING, message, **kwargs)

    def error(self, message: str, **kwargs: Any) -> None:
        """Log error message."""
        self._log(logging.ERROR, message, **kwargs)

    def _log(self, level: int, message: str, **kwargs: Any) -> None:
        """Internal log method with extra fields support."""
        if self._json_mode and kwargs:
            # For JSON mode, add extra fields to the record
            extra = {"extra_fields": kwargs}
            self.logger.log(level, message, extra=extra)
        else:
            # For console mode, append extra fields to message
            if kwargs:
                extra_str = " ".join(f"{k}={v!r}" for k, v in kwargs.items())
                message = f"{message} [{extra_str}]"
            self.logger.log(level, message)


def get_logger() -> RelayLogger:
    """Get the RelayLogger instance."""
    return RelayLogger()


def setup_logging(
    level: LogLevel | str | None = None,
    json_format: bool | None = None,
) -> RelayLogger:
    """Setup logging with configuration.

    Configuration priority:
    1. Function arguments
    2. Environment variables (RELAY_LOG_LEVEL, RELAY_LOG_FORMAT)
    3. Default values (INFO, console)

    Args:
        level: Log level (DEBUG, INFO, WARN, ERROR)
        json_format: Whether to use JSON format

    Returns:
        Configured RelayLogger instance
    """
    # Get from environment if not specified
    if level is None:
        level = os.environ.get("RELAY_LOG_LEVEL", "INFO")

    if json_format is None:
        json_format = os.environ.get("RELAY_LOG_FORMAT", "").lower() == "json"

    logger = RelayLogger()
    logger.setup(level=level, json_format=json_format)
    return logger
