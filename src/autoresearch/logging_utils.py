import logging
import sys
from typing import Optional

import structlog
from loguru import logger


def configure_logging(level: int = logging.INFO) -> None:
    """Configure structlog and loguru for unified logging."""
    logging.basicConfig(level=level, force=True)
    logger.remove()
    logger.add(sys.stderr, level=level)
    structlog.configure(
        wrapper_class=structlog.make_filtering_bound_logger(level),
        logger_factory=structlog.stdlib.LoggerFactory(),
    )


def get_logger(name: Optional[str] = None) -> structlog.BoundLogger:
    """Return a structlog logger instance."""
    return structlog.get_logger(name)

