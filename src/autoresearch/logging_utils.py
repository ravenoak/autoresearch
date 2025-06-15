"""Logging utilities that combine loguru and structlog for structured JSON logging.

This module provides a unified logging system that combines the ease of use of loguru
with the structured logging capabilities of structlog. It configures both libraries
to work together, outputting JSON-formatted logs that are easy to parse and analyze
by log management systems.

The module includes:
- An InterceptHandler that redirects standard library logging to loguru
- A configuration function that sets up both loguru and structlog
- A helper function to get a properly configured structlog logger

The logging system supports structured context data, which allows adding key-value
pairs to log messages that provide additional context for debugging and analysis.

Typical usage:
    ```python
    from autoresearch.logging_utils import configure_logging, get_logger
    import logging

    # Configure logging at application startup
    configure_logging(level=logging.DEBUG)

    # Get a logger for a specific component
    logger = get_logger("my_component")

    # Log messages with structured context
    logger.info("Operation started", operation="data_processing", user_id=123)

    # Log exceptions with context
    try:
        # Some operation that might fail
        result = process_data()
    except Exception as e:
        logger.exception("Operation failed", operation="data_processing", error=str(e))
    ```

The logging system is thread-safe and can be used throughout the application without
concerns about concurrency issues.
"""

from __future__ import annotations

import logging
import sys
from typing import Optional, cast

import structlog
from loguru import logger


class InterceptHandler(logging.Handler):
    """Handler that redirects standard library logging messages to loguru.

    This handler intercepts log records from the standard library logging module
    and redirects them to loguru, allowing all logs to be processed through the
    same pipeline regardless of their source.

    This is particularly useful when using third-party libraries that use the
    standard logging module, as it ensures their logs are formatted consistently
    with the rest of the application's logs and appear in the same output streams.

    The handler takes care to avoid issues with closed streams and handles
    level name mapping between the standard library and loguru.
    """

    def emit(self, record: logging.LogRecord) -> None:  # pragma: no cover
        if getattr(sys.stderr, "closed", False):
            return
        handlers = logger._core.handlers.values()  # type: ignore[attr-defined]
        for handler in handlers:
            stream = getattr(getattr(handler, "_sink", None), "_stream", None)
            if getattr(stream, "closed", False):
                return
        try:
            level: int | str = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno
        logger.log(level, record.getMessage())


def configure_logging(level: int = logging.INFO) -> None:
    """Configure loguru and structlog for unified JSON logging.

    This function sets up a unified logging system that combines loguru and structlog,
    configuring both to output JSON-formatted logs to stderr. It also redirects
    standard library logging to loguru using the InterceptHandler.

    The function configures:
    1. Standard library logging to use the InterceptHandler
    2. Loguru to output JSON-formatted logs to stderr
    3. Structlog to use ISO-formatted timestamps and JSON rendering

    This setup ensures that all logs, regardless of their source, are formatted
    consistently and can be easily parsed by log management systems.

    Args:
        level (int, optional): The minimum log level to capture. Uses the standard
            logging module level constants (DEBUG, INFO, WARNING, ERROR, CRITICAL).
            Defaults to logging.INFO.

    Returns:
        None

    Example:
        ```python
        import logging
        from autoresearch.logging_utils import configure_logging

        # Configure logging with DEBUG level
        configure_logging(level=logging.DEBUG)
        ```
    """

    logging.basicConfig(handlers=[InterceptHandler()], level=level, force=True)

    logger.remove()
    logger.add(sys.stderr, level=level, serialize=True)

    structlog.configure(
        wrapper_class=structlog.make_filtering_bound_logger(level),
        logger_factory=structlog.stdlib.LoggerFactory(),
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
    )


def get_logger(name: Optional[str] = None) -> structlog.BoundLogger:
    """Get a configured structlog logger instance.

    This function returns a structlog BoundLogger instance that is configured
    according to the settings applied by the configure_logging function. The
    logger supports structured logging with context data and outputs JSON-formatted
    logs.

    The returned logger provides methods like info(), debug(), warning(), error(),
    and exception() that accept both a message and arbitrary keyword arguments
    for structured context data.

    Args:
        name (Optional[str], optional): The name to associate with the logger,
            typically the module name or component name. If None, a default name
            is used. Defaults to None.

    Returns:
        structlog.BoundLogger: A configured structlog logger instance that
            supports structured logging with context data.

    Example:
        ```python
        logger = get_logger("auth_service")

        # Log with structured context
        logger.info("User logged in", user_id=123, ip_address="192.168.1.1")

        # Log an error with exception info
        try:
            # Some operation that might fail
            result = process_data()
        except Exception as e:
            logger.exception("Processing failed", data_id=42, error=str(e))
        ```
    """

    return cast(structlog.BoundLogger, structlog.get_logger(name))
