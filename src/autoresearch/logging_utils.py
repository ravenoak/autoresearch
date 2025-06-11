"""Logging helpers based on loguru and structlog."""

from __future__ import annotations

import logging
import sys
from typing import Optional

import structlog
from loguru import logger


class InterceptHandler(logging.Handler):
    """Redirect standard logging messages to loguru."""

    def emit(self, record: logging.LogRecord) -> None:  # pragma: no cover
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno
        logger.log(level, record.getMessage())


def configure_logging(level: int = logging.INFO) -> None:
    """Configure loguru and structlog for unified JSON logging."""

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
    """Return a structlog logger instance."""

    return structlog.get_logger(name)
