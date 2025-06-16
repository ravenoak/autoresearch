"""Error hierarchy for Autoresearch."""

from typing import Any, Dict, Optional, Type


class AutoresearchError(Exception):
    """Base class for all Autoresearch errors."""

    def __init__(
        self, message: str, cause: Optional[Exception] = None, **kwargs: Any
    ) -> None:
        """Initialize the error.

        Args:
            message: The error message
            cause: The original exception that caused this error
            **kwargs: Additional context for the error
        """
        self.message = message
        self.context = kwargs

        # Format the error message with context if provided
        if kwargs:
            context_str = ", ".join(
                f"{k}: {v}" for k, v in kwargs.items()
            )
            full_message = f"{message} ({context_str})"
        else:
            full_message = message

        super().__init__(full_message)

        # Set the cause of the exception
        if cause is not None:
            self.__cause__ = cause


class ConfigError(AutoresearchError):
    """Error related to configuration loading or validation."""


class AgentError(AutoresearchError):
    """Error related to agent operations."""

    def __init__(
        self, message: str, cause: Optional[Exception] = None, **kwargs: Any
    ) -> None:
        """Initialize the error with agent-specific context.

        Args:
            message: The error message
            cause: The original exception that caused this error
            **kwargs: Additional context for the error
        """
        # Rename agent_name to agent for better error messages
        if "agent_name" in kwargs:
            kwargs["agent"] = kwargs.pop("agent_name")

        super().__init__(message, cause, **kwargs)


class LLMError(AutoresearchError):
    """Error related to LLM operations."""

    def __init__(
        self, message: str, cause: Optional[Exception] = None, **kwargs: Any
    ) -> None:
        """Initialize the error with LLM-specific context.

        Args:
            message: The error message
            cause: The original exception that caused this error
            **kwargs: Additional context for the error
        """
        # Keep model as is for better error messages
        super().__init__(message, cause, **kwargs)


class StorageError(AutoresearchError):
    """Error related to storage operations."""


class SearchError(AutoresearchError):
    """Error related to search operations."""


class OrchestrationError(AutoresearchError):
    """Error related to orchestration operations."""


class ValidationError(AutoresearchError):
    """Error related to data validation."""


class TimeoutError(AutoresearchError):
    """Error raised when an operation times out."""

    def __init__(
        self, message: str, timeout: Optional[int] = None, 
        cause: Optional[Exception] = None, **kwargs: Any
    ) -> None:
        """Initialize the error with timeout-specific context.

        Args:
            message: The error message
            timeout: The timeout value in seconds
            cause: The original exception that caused this error
            **kwargs: Additional context for the error
        """
        if timeout is not None:
            kwargs["timeout"] = f"{timeout}s"

        super().__init__(message, cause, **kwargs)


class NotFoundError(AutoresearchError):
    """Error raised when a resource is not found."""

    def __init__(
        self, message: str, resource_type: Optional[str] = None,
        resource_id: Optional[str] = None, cause: Optional[Exception] = None,
        **kwargs: Any
    ) -> None:
        """Initialize the error with resource-specific context.

        Args:
            message: The error message
            resource_type: The type of resource that was not found
            resource_id: The ID of the resource that was not found
            cause: The original exception that caused this error
            **kwargs: Additional context for the error
        """
        if resource_type is not None:
            kwargs["resource_type"] = resource_type
        if resource_id is not None:
            kwargs["resource_id"] = resource_id

        super().__init__(message, cause, **kwargs)


class BackupError(AutoresearchError):
    """Error related to backup and restore operations."""

    def __init__(
        self, message: str, cause: Optional[Exception] = None, 
        suggestion: Optional[str] = None, **kwargs: Any
    ) -> None:
        """Initialize the error with backup-specific context.

        Args:
            message: The error message
            cause: The original exception that caused this error
            suggestion: A suggestion for how to fix the error
            **kwargs: Additional context for the error
        """
        if suggestion is not None:
            kwargs["suggestion"] = suggestion

        super().__init__(message, cause, **kwargs)
