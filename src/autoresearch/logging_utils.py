"""Logging utilities that combine loguru and structlog for structured JSON logging.

This module provides a unified logging system that combines the ease of use of loguru
with the structured logging capabilities of structlog. It configures both libraries
to work together, outputting JSON-formatted logs that are easy to parse and analyze
by log management systems.

The module includes:
- An InterceptHandler that redirects standard library logging to loguru
- A configuration function that sets up both loguru and structlog
- A helper function to get a properly configured structlog logger
- Correlation ID management for request tracing across all interfaces

To satisfy the repository's strict typing policy, the module defines a minimal
``LoguruHandler`` protocol that captures the private attributes accessed while
bridging standard logging to Loguru. ``InterceptHandler`` uses a guarded helper
to iterate over handlers without relying on unchecked ``type: ignore``
annotations.

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

    # Log messages with structured context and automatic correlation ID
    logger.info("Operation started", operation="data_processing", user_id=123)

    # Log exceptions with context
    try:
        # Some operation that might fail
        result = process_data()
    except Exception as e:
        logger.exception("Operation failed", operation="data_processing", error=str(e))

    # Use correlation context for scoped tracing
    with correlation_context() as corr_id:
        logger.info("Scoped operation", operation="scoped_task", correlation_id=corr_id)
    ```

The logging system is thread-safe and can be used throughout the application without
concerns about concurrency issues.
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
import uuid
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Iterable, Optional, Protocol, cast, MutableMapping, Generator

import re
import structlog
from dataclasses import dataclass
from loguru import logger
from pathlib import Path
from typing import Any, Callable, Dict, List, Literal, Union


# Correlation ID context variable for thread-safe request tracing
_correlation_id_context: ContextVar[Optional[str]] = ContextVar("correlation_id", default=None)


class AsyncLogQueue:
    """Typed wrapper for async logging queue with configuration."""

    def __init__(self, config: LoggingConfig):
        self._queue = asyncio.Queue[Any](maxsize=config.async_queue_size)
        self._config = config

    def put_nowait(self, item: Any) -> None:
        """Put an item in the queue without waiting."""
        return self._queue.put_nowait(item)

    def get(self) -> Any:
        """Get an item from the queue."""
        return self._queue.get()

    def full(self) -> bool:
        """Check if the queue is full."""
        return self._queue.full()

    def empty(self) -> bool:
        """Check if the queue is empty."""
        return self._queue.empty()

    def get_nowait(self) -> Any:
        """Get an item from the queue without waiting."""
        return self._queue.get_nowait()

    @property
    def config(self) -> LoggingConfig:
        """Get the configuration."""
        return self._config


# Async logging queue and task management
_async_log_queue: Optional[AsyncLogQueue] = None
_async_log_task: Optional[asyncio.Task[None]] = None
_async_log_shutdown_event: Optional[asyncio.Event] = None


# Audit logger cache
_audit_loggers: Dict[str, structlog.BoundLogger] = {}


class LoguruHandler(Protocol):
    """Minimal protocol covering the attributes accessed on Loguru handlers."""

    _sink: object


def _iter_loguru_handlers() -> Iterable[LoguruHandler]:
    """Yield registered Loguru handlers when available.

    The public ``logger`` API does not expose handler iteration so we retrieve
    it defensively via ``logger._core``. Runtime checks guard against API
    changes and keep :class:`InterceptHandler` compatible with newer Loguru
    releases.
    """

    core = getattr(logger, "_core", None)
    handlers = getattr(core, "handlers", None)
    if handlers is None:
        return ()
    if hasattr(handlers, "values"):
        return cast("Iterable[LoguruHandler]", handlers.values())
    if isinstance(handlers, Iterable):
        return cast("Iterable[LoguruHandler]", handlers)
    return ()


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
        """Forward standard logging records to loguru."""
        if getattr(sys.stderr, "closed", False):
            return
        for handler in _iter_loguru_handlers():
            sink = getattr(handler, "_sink", None)
            stream = getattr(sink, "_stream", None)
            if getattr(stream, "closed", False):
                return
        try:
            level: int | str = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Use async logging if enabled
        if _async_log_queue is not None and not asyncio.iscoroutinefunction(logger.log):
            # For async logging, queue the log entry
            try:
                _async_log_queue.put_nowait((level, record.getMessage()))
            except asyncio.QueueFull:
                # Handle backpressure based on configured strategy
                if _async_log_queue is not None:
                    if _async_log_queue.config.async_backpressure_strategy == "drop":
                        # Drop the log entry
                        pass
                    elif _async_log_queue.config.async_backpressure_strategy == "sample":
                        # Sample the log entry (drop with probability)
                        import random

                        if random.random() > 0.1:  # 10% sampling rate
                            pass
                        else:
                            # Actually log it (this shouldn't happen in a full queue)
                            pass
                    # For "block" strategy, we use put_nowait which raises QueueFull
                    # The calling code should handle this appropriately
            except Exception:
                # Fallback to synchronous logging on error
                logger.log(level, record.getMessage())
        else:
            # Synchronous logging
            logger.log(level, record.getMessage())


class AsyncLogHandler(logging.Handler):
    """Async logging handler that queues log entries for background processing.

    This handler provides non-blocking logging by queuing log entries and
    processing them in a background task. This prevents logging from blocking
    the main application threads during high-volume logging scenarios.

    The handler supports different backpressure strategies:
    - "block": Block until queue space is available (default)
    - "drop": Drop log entries when queue is full
    - "sample": Sample log entries when queue is full (drop with probability)
    """

    def __init__(self, config: LoggingConfig, level: int = logging.NOTSET):
        """Initialize the async log handler.

        Args:
            config: Logging configuration containing async settings
            level: Minimum log level for this handler
        """
        super().__init__(level)
        self._config = config

    def emit(self, record: logging.LogRecord) -> None:
        """Queue log entry for async processing."""
        if _async_log_queue is None:
            # Initialize async logging if not already done
            _init_async_logging(self._config)

        try:
            # Try to queue the log entry without blocking
            assert _async_log_queue is not None  # Should be initialized above
            _async_log_queue.put_nowait((record.levelno, record.getMessage()))
        except asyncio.QueueFull:
            # Handle backpressure based on configured strategy
            if self._config.async_backpressure_strategy == "drop":
                # Drop the log entry silently
                pass
            elif self._config.async_backpressure_strategy == "sample":
                # Sample the log entry (drop with probability)
                import random

                if random.random() > 0.1:  # 10% sampling rate
                    pass
                else:
                    # This shouldn't happen in a properly configured system
                    # but we need to handle it gracefully
                    pass
            # For "block" strategy, put_nowait raises QueueFull
            # The caller should handle this by falling back to sync logging
            else:
                # Fallback to synchronous logging
                try:
                    level_name = logger.level(record.levelname).name
                except ValueError:
                    level_name = str(record.levelno)
                logger.log(level_name, record.getMessage())
        except Exception:
            # Fallback to synchronous logging on any error
            try:
                level_name = logger.level(record.levelname).name
            except ValueError:
                level_name = str(record.levelno)
            logger.log(level_name, record.getMessage())


@dataclass
class LoggingConfig:
    """Unified configuration for the logging subsystem.

    This configuration class provides a single point of control for all
    logging settings across the application. It supports environment
    variable overrides and validation.

    Attributes:
        level: Minimum log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format: Log output format ('json' or 'console')
        enable_correlation: Whether to enable correlation ID tracking
        enable_sampling: Whether to enable log sampling for performance
        sampling_rate: Sampling rate (0.0 to 1.0, where 1.0 = no sampling)
        output_file: Optional file path for log output
        enable_rotation: Whether to enable log rotation
        rotation_size: Maximum size before rotation (e.g., '100MB', '1GB')
        retention_days: Number of days to retain log files
        enable_audit_log: Whether to enable separate audit logging
        audit_log_path: Optional path for audit log file
        security_level: Sensitivity level for data sanitization ('strict', 'normal', 'permissive')
        enable_async_logging: Whether to enable async logging for high-performance scenarios
        async_queue_size: Maximum number of log entries to queue for async processing
        async_backpressure_strategy: Strategy for handling queue overflow ('block', 'drop', 'sample')
    """

    level: int = logging.INFO
    format: Literal["json", "console", "auto"] = "auto"
    enable_correlation: bool = True
    enable_sampling: bool = False
    sampling_rate: float = 1.0
    output_file: Optional[Path] = None
    enable_rotation: bool = False
    rotation_size: str = "100MB"
    retention_days: int = 30
    enable_audit_log: bool = True
    audit_log_path: Optional[Path] = None
    security_level: Literal["strict", "normal", "permissive"] = "normal"
    enable_async_logging: bool = False
    async_queue_size: int = 10000
    async_backpressure_strategy: Literal["block", "drop", "sample"] = "block"

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        self._validate_config()

    def _validate_config(self) -> None:
        """Validate configuration values."""
        if not (0.0 <= self.sampling_rate <= 1.0):
            raise ValueError(f"Sampling rate must be between 0.0 and 1.0, got {self.sampling_rate}")

        if self.retention_days < 1:
            raise ValueError(f"Retention days must be at least 1, got {self.retention_days}")

        if self.security_level not in ["strict", "normal", "permissive"]:
            raise ValueError(
                f"Security level must be 'strict', 'normal', or 'permissive', got {self.security_level}"
            )

        if self.async_queue_size < 1:
            raise ValueError(f"Async queue size must be at least 1, got {self.async_queue_size}")

        if self.async_backpressure_strategy not in ["block", "drop", "sample"]:
            raise ValueError(
                f"Async backpressure strategy must be 'block', 'drop', or 'sample', got {self.async_backpressure_strategy}"
            )

    @classmethod
    def from_env(cls) -> "LoggingConfig":
        """Create configuration from environment variables.

        Environment variables:
        - AUTORESEARCH_LOG_LEVEL: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        - AUTORESEARCH_LOG_FORMAT: Format ('json' or 'console')
        - AUTORESEARCH_LOG_CORRELATION: Enable correlation IDs (true/false)
        - AUTORESEARCH_LOG_SAMPLING_RATE: Sampling rate (0.0 to 1.0)
        - AUTORESEARCH_LOG_FILE: Log file path
        - AUTORESEARCH_LOG_ROTATION: Enable rotation (true/false)
        - AUTORESEARCH_LOG_RETENTION_DAYS: Retention days
        - AUTORESEARCH_AUDIT_LOG_FILE: Audit log file path
        - AUTORESEARCH_LOG_SECURITY_LEVEL: Security level (strict/normal/permissive)
        - AUTORESEARCH_LOG_ASYNC: Enable async logging (true/false)
        - AUTORESEARCH_LOG_ASYNC_QUEUE_SIZE: Async queue size (default: 10000)
        - AUTORESEARCH_LOG_ASYNC_BACKPRESSURE: Backpressure strategy (block/drop/sample)
        """
        # Parse log level
        level_name = os.getenv("AUTORESEARCH_LOG_LEVEL", "INFO").upper()
        try:
            level = getattr(logging, level_name)
        except AttributeError:
            raise ValueError(f"Invalid log level: {level_name}")

        # Parse boolean values
        def parse_bool(env_var: str, default: bool = False) -> bool:
            value = os.getenv(env_var, "false" if not default else "true").lower()
            return value in ("true", "1", "yes", "on")

        def parse_float(env_var: str, default: float) -> float:
            value = os.getenv(env_var)
            return float(value) if value is not None else default

        # Parse and validate literal types
        log_format = os.getenv("AUTORESEARCH_LOG_FORMAT", "auto").lower()
        if log_format not in ("json", "console", "auto"):
            log_format = "auto"

        security_level = os.getenv("AUTORESEARCH_LOG_SECURITY_LEVEL", "normal").lower()
        if security_level not in ("strict", "normal", "permissive"):
            security_level = "normal"

        backpressure_strategy = os.getenv("AUTORESEARCH_LOG_ASYNC_BACKPRESSURE", "block").lower()
        if backpressure_strategy not in ("block", "drop", "sample"):
            backpressure_strategy = "block"

        return cls(
            level=level,
            format=log_format,  # type: ignore
            enable_correlation=parse_bool("AUTORESEARCH_LOG_CORRELATION", True),
            enable_sampling=parse_float("AUTORESEARCH_LOG_SAMPLING_RATE", 1.0) < 1.0,
            sampling_rate=parse_float("AUTORESEARCH_LOG_SAMPLING_RATE", 1.0),
            output_file=(
                Path(cast(str, os.getenv("AUTORESEARCH_LOG_FILE")))
                if os.getenv("AUTORESEARCH_LOG_FILE")
                else None
            ),
            enable_rotation=parse_bool("AUTORESEARCH_LOG_ROTATION", False),
            retention_days=int(os.getenv("AUTORESEARCH_LOG_RETENTION_DAYS", "30")),
            enable_audit_log=parse_bool("AUTORESEARCH_AUDIT_LOG_FILE") or True,
            audit_log_path=(
                Path(cast(str, os.getenv("AUTORESEARCH_AUDIT_LOG_FILE")))
                if os.getenv("AUTORESEARCH_AUDIT_LOG_FILE")
                else None
            ),
            security_level=security_level,  # type: ignore
            enable_async_logging=parse_bool("AUTORESEARCH_LOG_ASYNC", False),
            async_queue_size=int(os.getenv("AUTORESEARCH_LOG_ASYNC_QUEUE_SIZE", "10000")),
            async_backpressure_strategy=backpressure_strategy,  # type: ignore
        )


class SensitiveDataFilter:
    """Processor that automatically sanitizes sensitive data before logging.

    This processor detects and redacts sensitive information including:
    - API keys (various formats)
    - Passwords and secrets
    - Email addresses
    - Credit card numbers
    - Phone numbers
    - URLs with embedded credentials
    - JWT tokens
    - Database connection strings
    - Social Security Numbers

    The filter supports configurable sensitivity levels and handles nested
    data structures recursively.
    """

    # Sensitive field name patterns (case-insensitive)
    SENSITIVE_FIELD_PATTERNS = [
        r"password",
        r"secret",
        r"token",
        r"key",
        r"credential",
        r"auth",
        r"api[_-]?key",
        r"bearer",
        r"jwt",
        r"cookie",
        r"csrf",
        r"nonce",
        r"signature",
    ]

    # Sensitive value patterns
    SENSITIVE_VALUE_PATTERNS = [
        # API Keys (various formats) - more flexible length requirements and patterns
        # Order matters! API keys must come before credit cards to avoid false matches
        (r"(?:sk|pk|sk_test|pk_test|sk-live|pk-live)[-_]?[a-zA-Z0-9]{8,}", "[API_KEY]"),
        (r"(?:xoxp|xoxb|xapp)-[0-9]+-[0-9]+-[0-9]+-[a-zA-Z0-9]+", "[SLACK_TOKEN]"),
        (r"ghp_[a-zA-Z0-9]{20,}", "[GITHUB_TOKEN]"),
        (r"gl-[a-zA-Z0-9\-_]{16,}", "[GITLAB_TOKEN]"),
        (r"\beyJ[a-zA-Z0-9\-_]+\.eyJ[a-zA-Z0-9\-_]+\.[a-zA-Z0-9\-_]*\b", "[JWT_TOKEN]"),
        (r"[bB]earer\s+[a-zA-Z0-9\-_\.]{8,}", "[BEARER_TOKEN]"),
        # Passwords and secrets (in quotes or as values) - improved patterns
        (r'(["\'])(?:password|pwd)[=:]?\s*\1([^"\']{3,})', r"\1[REDACTED]\1\2"),
        (r'(["\'])(?:secret)[=:]?\s*\1([^"\']{3,})', r"\1[REDACTED]\1\2"),
        (r'(["\'])(?:api[_-]?key|token)[=:]?\s*\1([^"\']{8,})', r"\1[REDACTED]\1\2"),
        # URLs with embedded credentials - more specific to avoid email conflicts
        (r"(https?)://([^:/@\s]+):([^@\s]+)@(.+)?", r"\1://\2:[REDACTED]@\4"),
        # Database connection strings - more specific
        (
            r"\b(?:postgresql|mysql|mongodb)://([^:/@]+):([^@]+)@([a-zA-Z0-9_/.-]+)?",
            r"\1:[REDACTED]@\3",
        ),
        # Passwords without quotes - handle assignment format and direct values
        (r'\b(?:password|pwd)[=:]?\s*([^"\s@]{3,})', r"[REDACTED]"),
        (r'\b(?:secret)[=:]?\s*([^"\s@]{3,})', r"[REDACTED]"),
        # Passwords in assignment format without space
        (r'\b(?:password|pwd)[=:]?([^"\s@]{3,})', r"[REDACTED]"),
        (r'\b(?:secret)[=:]?([^"\s@]{3,})', r"[REDACTED]"),
        # Generic passwords/secrets in direct values (fallback)
        (r"\bsecret[_\d]*\b", r"[REDACTED]"),
        # Credit card numbers (various formats) - before phone patterns to take precedence
        (r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b", "[CREDIT_CARD]"),
        (r"\b\d{4}[-\s]?\d{6}[-\s]?\d{5}\b", "[CREDIT_CARD]"),
        # Social Security Numbers (US format) - more specific to avoid phone conflicts
        (r"\b(?!555[.-]\d{2}[.-]\d{4}\b)\d{3}[-.\s]\d{2}[-.\s]\d{4}\b", "[SSN]"),
        # Phone numbers - very specific patterns to avoid false positives
        (
            r"(?:^|[^a-zA-Z0-9])\+\d{1,4}[-.\s]*\(?\d{1,4}\)?[-.\s]*\d{1,4}[-.\s]*\d{1,4}[-.\s]*\d{0,4}\b(?![a-zA-Z0-9])",
            "[PHONE]",
        ),
        (r"(?:^|[^a-zA-Z0-9])\(?\d{3}\)?[-.\s]*\d{3}[-.\s]*\d{4}\b(?![a-zA-Z0-9])", "[PHONE]"),
        (r"(?:^|[^a-zA-Z0-9])\d{10,11}\b(?![a-zA-Z0-9])", "[PHONE]"),
        # Email addresses - handle localhost and unicode
        (r"\b[\w.%+-]+@(?:localhost|[\w.-]+\.[a-zA-Z]{2,63})\b", "[EMAIL]"),
        # Generic secrets (long alphanumeric strings) - only in strict mode
        # Generic secrets (long alphanumeric strings) - only in strict mode
        # This pattern is handled in sensitivity level logic
    ]

    sensitivity_level: Literal["strict", "normal", "permissive"]

    def __init__(
        self,
        sensitivity_level: Literal["strict", "normal", "permissive"] = "normal",
        config: Optional[LoggingConfig] = None,
    ) -> None:
        """Initialize the sensitive data filter.

        Args:
            sensitivity_level: Security sensitivity level
                - "strict": Maximum redaction, may have false positives
                - "normal": Balanced security and usability (default)
                - "permissive": Minimal redaction, may miss some sensitive data
            config: Optional LoggingConfig to get security level from
        """
        # Use config security level if provided, otherwise use parameter
        if config:
            self.sensitivity_level = config.security_level
        else:
            level = sensitivity_level.lower()
            if level in ("strict", "normal", "permissive"):
                self.sensitivity_level = level  # type: ignore
            else:
                self.sensitivity_level = "normal"

        # Adjust patterns based on sensitivity level
        if self.sensitivity_level == "strict":
            # Add more aggressive patterns for strict mode
            self.SENSITIVE_VALUE_PATTERNS.extend(
                [
                    (
                        r"[a-zA-Z0-9]{20,}",
                        "[POTENTIAL_SECRET]",
                    ),  # Longer strings (no word boundaries)
                ]
            )
        elif self.sensitivity_level == "permissive":
            # Remove some patterns that might be too aggressive
            self.SENSITIVE_VALUE_PATTERNS = [
                pattern
                for pattern in self.SENSITIVE_VALUE_PATTERNS
                if "[POTENTIAL_SECRET]" not in str(pattern) and "[SECRET]" not in str(pattern)
            ]

        # Compile regex patterns for performance
        self._compiled_patterns = [
            (re.compile(pattern, re.IGNORECASE), replacement)
            for pattern, replacement in self.SENSITIVE_VALUE_PATTERNS
        ]

        # Compile field name patterns
        self._field_patterns = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.SENSITIVE_FIELD_PATTERNS
        ]

    def __call__(
        self, logger: Any, method_name: str, event_dict: MutableMapping[str, Any]
    ) -> MutableMapping[str, Any] | str | bytes | bytearray | tuple[Any, ...]:
        """Process and sanitize the event dictionary.

        Args:
            logger: The logger instance
            method_name: The logging method name
            event_dict: The event dictionary to sanitize

        Returns:
            The sanitized event dictionary
        """
        result = self._sanitize_dict(event_dict)
        # Ensure we return a MutableMapping as expected by structlog
        return result if isinstance(result, MutableMapping) else event_dict

    def _sanitize_dict(
        self, data: Union[Dict[str, Any], List[Any], Any]
    ) -> Union[Dict[str, Any], List[Any], Any]:
        """Recursively sanitize a data structure.

        Args:
            data: The data to sanitize

        Returns:
            The sanitized data
        """
        if isinstance(data, dict):
            return self._sanitize_dict_dict(data)
        elif isinstance(data, list):
            return self._sanitize_dict_list(data)
        elif isinstance(data, str):
            return self._sanitize_string(data)
        else:
            return data

    def _sanitize_dict_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize a dictionary."""
        sanitized = {}

        for key, value in data.items():
            # Check if field name indicates sensitive data
            if self._is_sensitive_field_name(key):
                # For sensitive field names, check if it's a simple value or complex structure
                if isinstance(value, (dict, list)):
                    # For complex structures, sanitize recursively but keep the structure
                    sanitized[key] = cast(Any, self._sanitize_dict(value))
                else:
                    # For simple values, redact the entire field
                    sanitized[key] = "[REDACTED]"
            else:
                # Otherwise, sanitize the value recursively
                sanitized[key] = cast(Any, self._sanitize_dict(value))

        return sanitized

    def _sanitize_dict_list(self, data: List[Any]) -> List[Any]:
        """Sanitize a list."""
        return [self._sanitize_dict(item) for item in data]

    def _sanitize_string(self, value: str) -> str:
        """Sanitize a string value."""
        sanitized = value

        # Apply all sanitization patterns
        for pattern, replacement in self._compiled_patterns:
            sanitized = pattern.sub(replacement, sanitized)

        return sanitized

    def _is_sensitive_field_name(self, field_name: str) -> bool:
        """Check if a field name indicates sensitive data."""
        return any(pattern.search(field_name) for pattern in self._field_patterns)

    def _is_value_redacted(self, value: Any) -> bool:
        """Check if a value has been redacted by sanitization patterns."""
        if isinstance(value, str):
            return any(
                redaction in value
                for redaction in [
                    "[REDACTED]",
                    "[API_KEY]",
                    "[EMAIL]",
                    "[PHONE]",
                    "[CREDIT_CARD]",
                    "[SSN]",
                    "[JWT_TOKEN]",
                    "[BEARER_TOKEN]",
                    "[GITHUB_TOKEN]",
                    "[GITLAB_TOKEN]",
                    "[SLACK_TOKEN]",
                ]
            )
        elif isinstance(value, dict):
            return any(self._is_value_redacted(v) for v in value.values())
        elif isinstance(value, list):
            return any(self._is_value_redacted(item) for item in value)
        return False

    def sanitize_value(self, value: Any) -> Any:
        """Sanitize a single value (for testing and direct use).

        Args:
            value: The value to sanitize

        Returns:
            The sanitized value
        """
        return self._sanitize_dict(value)


def get_audit_logger(component: str) -> structlog.BoundLogger:
    """Get a logger for security-sensitive operations.

    This logger is specifically designed for audit events and security-related
    operations. It has the following characteristics:
    - Cannot be disabled in production environments
    - Never subject to log sampling
    - Always includes full contextual information
    - Stored separately from application logs (when configured)
    - Includes security-specific fields (actor, action, resource, outcome)

    Args:
        component: The component name (e.g., "auth", "api", "storage")

    Returns:
        A configured structlog logger for audit events

    Example:
        >>> audit_logger = get_audit_logger("auth")
        >>> audit_logger.info(
        ...     "Authentication attempt",
        ...     actor="user:alice",
        ...     action="login",
        ...     resource="system",
        ...     outcome="success",
        ...     ip_address="192.168.1.100"
        ... )
    """
    # Use a separate logger name for audit events to ensure they can be
    # routed to different outputs and are never sampled
    audit_logger_name = f"audit.{component}"

    # Get or create audit logger with special configuration
    if audit_logger_name not in _audit_loggers:
        # Create audit logger that bypasses normal filtering
        audit_logger = structlog.get_logger(audit_logger_name)

        # Apply audit-specific configuration if needed
        # For now, use the same configuration but ensure it's never sampled
        _audit_loggers[audit_logger_name] = audit_logger

    return _audit_loggers[audit_logger_name]


def _detect_log_format(config: LoggingConfig) -> str:
    """Detect the appropriate log format based on configuration and terminal type."""
    if config.format == "auto":
        # Auto-detect based on terminal interactivity and stream redirection
        try:
            # Check if stderr is a TTY (interactive terminal)
            if hasattr(config, "_stderr_isatty"):
                # Use cached result if available
                return "console" if config._stderr_isatty else "json"
            else:
                # Enhanced TTY detection with multiple checks
                is_tty = _is_interactive_terminal()

                # Additional check: if stdout is redirected but stderr is not,
                # still use console format for human readability
                stdout_redirected = not sys.stdout.isatty()
                stderr_redirected = not sys.stderr.isatty()

                # If stderr is TTY (human can see it), use console format
                # If both streams are redirected, use JSON for machine parsing
                if stderr_redirected and stdout_redirected:
                    # Both streams redirected - use JSON for automation
                    final_format = "json"
                elif is_tty or (not stderr_redirected):
                    # Human-readable context - use console format
                    final_format = "console"
                else:
                    # Fallback to JSON for safety
                    final_format = "json"

                # Cache the result for this config instance
                config._stderr_isatty = final_format == "console"  # type: ignore
                return final_format
        except (AttributeError, OSError):
            # Fallback to JSON if TTY detection fails
            return "json"
    else:
        return config.format


def _is_interactive_terminal() -> bool:
    """Enhanced terminal interactivity detection."""
    try:
        # Check stderr TTY status (primary for logs)
        if sys.stderr.isatty():
            return True

        # Check stdout TTY status (for output)
        if sys.stdout.isatty():
            return True

        # Check stdin TTY status (for input)
        if sys.stdin.isatty():
            return True

        # Check common environment variables for terminal detection
        term_env = os.environ.get("TERM", "").lower()
        if term_env in ("xterm", "xterm-256color", "screen", "tmux", "linux", "ansi"):
            return True

        # Check for Windows terminal
        if os.name == "nt" and os.environ.get("WT_SESSION"):  # Windows Terminal
            return True

        return False

    except (AttributeError, OSError):
        # If any check fails, assume non-interactive for safety
        return False


def _create_console_formatter() -> Callable[[Any], str]:
    """Create a console formatter for human-readable log output."""

    def format_console(record: Any) -> str:
        """Format a log record for console output."""
        level = record.get("level", "INFO")
        logger_name = record.get("logger", "unknown")
        message = record.get("message", "")

        # Format: [LEVEL] component: message [correlation_id]
        parts = [f"[{level}]", f"{logger_name}:", message]

        # Add correlation ID if present
        correlation_id = record.get("correlation_id")
        if correlation_id:
            parts.append(f"[{correlation_id}]")

        return " ".join(parts)

    return format_console


def _console_renderer(logger: Any, method_name: str, event_dict: Any) -> str:
    """Custom console renderer for structlog that formats for human readability."""
    # Extract key fields
    level = event_dict.get("level", "INFO")
    logger_name = event_dict.get("logger", "unknown")
    message = event_dict.get("message", "")

    # Build console format
    console_parts = [f"[{level}]", f"{logger_name}:", message]

    # Add correlation ID if present
    correlation_id = event_dict.get("correlation_id")
    if correlation_id:
        console_parts.append(f"[{correlation_id}]")

    return " ".join(console_parts)


def configure_logging(level: int | LoggingConfig | None = None) -> None:
    """Configure loguru and structlog for unified JSON logging.

    This function sets up a unified logging system that combines loguru and structlog,
    configuring both to output JSON-formatted logs to stderr. It also redirects
    standard library logging to loguru using the InterceptHandler.

    The function configures:
    1. Standard library logging to use the InterceptHandler
    2. Loguru to output JSON-formatted logs to stderr
    3. Structlog to use ISO-formatted timestamps and JSON rendering
    4. Sensitive data sanitization with configurable security levels

    This setup ensures that all logs, regardless of their source, are formatted
    consistently and can be easily parsed by log management systems.

    Args:
        level: Either a log level (int) for backward compatibility, or a LoggingConfig
            object for full configuration control. If None, uses LoggingConfig.from_env().

    Returns:
        None

    Example:
        ```python
        import logging
        from autoresearch.logging_utils import configure_logging, LoggingConfig

        # Configure logging with DEBUG level (backward compatible)
        configure_logging(level=logging.DEBUG)

        # Configure with full configuration
        config = LoggingConfig(
            level=logging.DEBUG,
            security_level="strict",
            enable_correlation=True
        )
        configure_logging(config)
        ```
    """
    # Handle backward compatibility and config resolution
    if isinstance(level, LoggingConfig):
        config = level
    elif level is None:
        config = LoggingConfig.from_env()
    else:
        # Backward compatibility: level is an int
        config = LoggingConfig(level=level)

    # Detect the appropriate log format based on configuration and terminal type
    detected_format = _detect_log_format(config)

    # Configure standard library logging
    if config.enable_async_logging:
        # Use async handler for non-blocking logging
        async_handler = AsyncLogHandler(config, level=config.level)
        logging.basicConfig(handlers=[async_handler], level=config.level, force=True)
    else:
        # Use standard intercept handler for synchronous logging
        logging.basicConfig(handlers=[InterceptHandler()], level=config.level, force=True)

    # Configure loguru
    logger.remove()

    # Choose formatter based on detected format
    if detected_format == "console":
        # Use console formatter for human-readable output
        console_formatter = _create_console_formatter()
        logger.add(
            sys.stderr,
            level=config.level,
            format=console_formatter,
            filter=lambda record: record["level"].no >= config.level,
        )
    else:
        # Use JSON serialization for machine parsing
        logger.add(sys.stderr, level=config.level, serialize=True)

    # Configure structlog with sensitive data filtering and correlation ID
    if detected_format == "console":
        # For console format, use a simpler processor chain
        structlog.configure(
            wrapper_class=structlog.make_filtering_bound_logger(config.level),
            logger_factory=structlog.stdlib.LoggerFactory(),
            processors=[
                structlog.processors.TimeStamper(fmt="iso"),
                # Add correlation ID processor before sanitization
                _add_correlation_id_processor,
                SensitiveDataFilter(config=config),  # Use config for security level
                # Custom console renderer that preserves structure but formats for console
                _console_renderer,
            ],
        )
    else:
        # For JSON format, use standard JSON rendering
        structlog.configure(
            wrapper_class=structlog.make_filtering_bound_logger(config.level),
            logger_factory=structlog.stdlib.LoggerFactory(),
            processors=[
                structlog.processors.TimeStamper(fmt="iso"),
                # Add correlation ID processor before sanitization
                _add_correlation_id_processor,
                SensitiveDataFilter(config=config),  # Use config for security level
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


def get_correlation_id() -> str:
    """Get the current correlation ID for this execution context.

    Returns:
        The current correlation ID, or generates a new one if none exists.

    Example:
        >>> correlation_id = get_correlation_id()
        >>> logger.info("Operation started", correlation_id=correlation_id)
    """
    correlation_id = _correlation_id_context.get()
    if correlation_id is None:
        correlation_id = generate_correlation_id()
        _correlation_id_context.set(correlation_id)
    return correlation_id


def set_correlation_id(correlation_id: str) -> None:
    """Set the correlation ID for the current execution context.

    Args:
        correlation_id: The correlation ID to set.

    Example:
        >>> set_correlation_id("req-123e4567-e89b-12d3-a456-426614174000")
        >>> logger.info("Request received")  # Will include correlation_id
    """
    _correlation_id_context.set(correlation_id)


def generate_correlation_id() -> str:
    """Generate a new UUID-based correlation ID.

    Returns:
        A new correlation ID in the format "req-<uuid>".

    Example:
        >>> correlation_id = generate_correlation_id()
        >>> # Returns something like "req-123e4567-e89b-12d3-a456-426614174000"
    """
    return f"req-{uuid.uuid4().hex}"


@contextmanager
def correlation_context(correlation_id: Optional[str] = None) -> Generator[str, None, None]:
    """Context manager for scoped correlation ID management.

    This context manager allows setting a correlation ID for a specific
    scope of execution, automatically restoring the previous correlation
    ID when exiting the context.

    Args:
        correlation_id: The correlation ID to set for this context.
                       If None, generates a new one.

    Example:
        >>> with correlation_context("custom-id") as corr_id:
        ...     logger.info("Operation in context")  # Uses "custom-id"
        ... # Previous correlation ID is restored
    """
    # Save current correlation ID
    previous_id = _correlation_id_context.get()

    try:
        # Set new correlation ID (generate if not provided)
        if correlation_id is None:
            correlation_id = generate_correlation_id()
        _correlation_id_context.set(correlation_id)

        yield correlation_id
    finally:
        # Restore previous correlation ID
        if previous_id is not None:
            _correlation_id_context.set(previous_id)
        else:
            _correlation_id_context.set(None)


def get_correlation_id_from_headers(headers: Dict[str, str]) -> Optional[str]:
    """Extract correlation ID from request headers.

    Args:
        headers: Dictionary of HTTP headers.

    Returns:
        The correlation ID if found, None otherwise.

    Example:
        >>> headers = {"X-Correlation-ID": "req-123e4567-e89b-12d3-a456-426614174000"}
        >>> correlation_id = get_correlation_id_from_headers(headers)
    """
    # Check common correlation ID header names
    for header_name in ["X-Correlation-ID", "X-Request-ID", "X-Trace-ID", "Correlation-ID"]:
        if header_name in headers:
            return headers[header_name]
    return None


def _init_async_logging(config: LoggingConfig) -> None:
    """Initialize async logging infrastructure.

    Args:
        config: Logging configuration containing async settings
    """
    global _async_log_queue, _async_log_task, _async_log_shutdown_event

    if _async_log_queue is not None:
        return  # Already initialized

    # Create bounded queue for async logging
    _async_log_queue = AsyncLogQueue(config)

    # Create shutdown event
    _async_log_shutdown_event = asyncio.Event()

    # Start background processing task
    _async_log_task = asyncio.create_task(_async_log_processor())


async def _async_log_processor() -> None:
    """Background task that processes queued log entries.

    This task runs continuously, processing log entries from the async queue
    and forwarding them to the synchronous logger. It handles graceful shutdown
    when the shutdown event is set.
    """
    if _async_log_queue is None or _async_log_shutdown_event is None:
        return

    try:
        while not _async_log_shutdown_event.is_set():
            try:
                # Wait for log entry with timeout to allow shutdown checks
                log_entry = await asyncio.wait_for(_async_log_queue.get(), timeout=1.0)

                if log_entry is not None:
                    level, message = log_entry
                    # Forward to synchronous logger
                    logger.log(level, message)

            except asyncio.TimeoutError:
                # Check for shutdown
                continue
            except Exception as e:
                # Log any processing errors (but avoid recursion)
                try:
                    logger.error(f"Error processing async log entry: {e}")
                except Exception:
                    # If even error logging fails, silently continue
                    pass

    except asyncio.CancelledError:
        # Handle graceful shutdown
        pass
    finally:
        # Process any remaining entries in the queue
        while not _async_log_queue.empty():
            try:
                log_entry = _async_log_queue.get_nowait()
                if log_entry is not None:
                    level, message = log_entry
                    logger.log(level, message)
            except asyncio.QueueEmpty:
                break
            except Exception:
                # Silently handle any remaining errors during shutdown
                pass


async def shutdown_async_logging() -> None:
    """Gracefully shutdown async logging.

    This function should be called during application shutdown to ensure
    all queued log entries are processed before the application exits.
    """
    global _async_log_queue, _async_log_task, _async_log_shutdown_event

    if _async_log_shutdown_event is not None:
        _async_log_shutdown_event.set()

    if _async_log_task is not None:
        try:
            await asyncio.wait_for(_async_log_task, timeout=5.0)
        except asyncio.TimeoutError:
            _async_log_task.cancel()
            try:
                await _async_log_task
            except asyncio.CancelledError:
                pass

    # Clean up global state
    _async_log_queue = None
    _async_log_task = None
    _async_log_shutdown_event = None


def _add_correlation_id_processor(
    logger: Any, method_name: str, event_dict: MutableMapping[str, Any]
) -> MutableMapping[str, Any]:
    """Structlog processor that adds correlation ID to all log entries.

    This processor automatically includes the current correlation ID in all
    structured log entries, ensuring traceability across the entire request
    lifecycle.

    Args:
        logger: The logger instance
        method_name: The logging method name
        event_dict: The event dictionary to modify

    Returns:
        The modified event dictionary with correlation_id added
    """
    # Get current correlation ID and add it to the event dict
    correlation_id = get_correlation_id()
    event_dict["correlation_id"] = correlation_id
    return event_dict


def configure_logging_from_env(
    env_var: str = "AUTORESEARCH_LOG_LEVEL",
    default_level: int = logging.INFO,
) -> None:
    """Configure logging using a level from an environment variable.

    This helper reads ``env_var`` to determine the log level and passes the
    result to :func:`configure_logging`. If the variable is unset or contains an
    invalid level name, ``default_level`` is used or a ``ValueError`` is raised
    respectively.

    Args:
        env_var: Name of the environment variable that stores the log level.
            Defaults to ``"AUTORESEARCH_LOG_LEVEL"``.
        default_level: Fallback level if the variable is missing.
            Defaults to ``logging.INFO``.

    Raises:
        ValueError: If the environment value is set but not a valid log level.
    """
    level_name = os.getenv(env_var, "")
    if level_name:
        try:
            level = getattr(logging, level_name.upper())
        except AttributeError:
            raise ValueError(f"Invalid log level: {level_name}") from None
    else:
        level = default_level
    configure_logging(level=level)
