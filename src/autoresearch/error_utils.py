"""Error handling utilities for consistent error reporting across interfaces.

This module provides utilities for consistent error handling and reporting across
all interfaces (CLI, GUI, API, A2A/MCP). It includes functions for formatting error
messages with actionable suggestions and code examples.
"""

from typing import Dict, Any, Optional, Tuple, List, Union
import traceback
import logging
from enum import Enum

from .errors import AutoresearchError, ConfigError, AgentError, LLMError, StorageError, SearchError, OrchestrationError, ValidationError, TimeoutError, NotFoundError, BackupError

# Get logger
logger = logging.getLogger(__name__)

class ErrorSeverity(str, Enum):
    """Enumeration of error severity levels."""
    CRITICAL = "critical"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

class ErrorInfo:
    """Container for error information with consistent structure across interfaces."""
    
    def __init__(
        self,
        message: str,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        exception: Optional[Exception] = None,
        suggestions: Optional[List[str]] = None,
        code_examples: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize error information.
        
        Args:
            message: The error message
            severity: The severity level of the error
            exception: The original exception that caused this error
            suggestions: List of actionable suggestions for resolving the error
            code_examples: List of code examples for resolving the error
            context: Additional context for the error
        """
        self.message = message
        self.severity = severity
        self.exception = exception
        self.suggestions = suggestions or []
        self.code_examples = code_examples or []
        self.context = context or {}
        
        # Get traceback if exception is provided
        self.traceback = None
        if exception is not None:
            self.traceback = traceback.format_exception(
                type(exception), exception, exception.__traceback__
            )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error information to a dictionary.
        
        Returns:
            A dictionary representation of the error information
        """
        return {
            "message": self.message,
            "severity": self.severity,
            "suggestions": self.suggestions,
            "code_examples": self.code_examples,
            "context": self.context,
            "exception_type": type(self.exception).__name__ if self.exception else None,
            "traceback": self.traceback,
        }
    
    def __str__(self) -> str:
        """Get string representation of error information.
        
        Returns:
            A string representation of the error information
        """
        parts = [f"{self.severity.upper()}: {self.message}"]
        
        if self.suggestions:
            parts.append("\nSuggestions:")
            for suggestion in self.suggestions:
                parts.append(f"  - {suggestion}")
        
        if self.code_examples:
            parts.append("\nExamples:")
            for example in self.code_examples:
                parts.append(f"  {example}")
        
        if self.context:
            parts.append("\nContext:")
            for key, value in self.context.items():
                parts.append(f"  {key}: {value}")
        
        return "\n".join(parts)

def get_error_info(exception: Exception) -> ErrorInfo:
    """Get error information from an exception.
    
    This function extracts error information from an exception, including
    suggestions and code examples for common error types.
    
    Args:
        exception: The exception to extract information from
        
    Returns:
        An ErrorInfo object containing the extracted information
    """
    # Default values
    message = str(exception)
    severity = ErrorSeverity.ERROR
    suggestions = []
    code_examples = []
    context = {}
    
    # Extract context from AutoresearchError
    if isinstance(exception, AutoresearchError):
        context = exception.context
    
    # Handle specific error types
    if isinstance(exception, ConfigError):
        suggestions.append("Check your configuration file for syntax errors.")
        suggestions.append("Make sure all required fields are present.")
        code_examples.append("autoresearch config validate")
        code_examples.append("autoresearch config init --force")
    
    elif isinstance(exception, AgentError):
        suggestions.append("Check the agent implementation for errors.")
        if "agent" in context:
            suggestions.append(f"Make sure the {context['agent']} agent is properly configured.")
    
    elif isinstance(exception, LLMError):
        suggestions.append("Check your LLM backend configuration.")
        if "model" in context:
            suggestions.append(f"Make sure the {context['model']} model is available.")
        if "api_key" in str(exception).lower():
            suggestions.append("Make sure your API key is set correctly in the .env file.")
            code_examples.append("OPENAI_API_KEY=your-api-key")
    
    elif isinstance(exception, StorageError):
        suggestions.append("Check your storage configuration.")
        suggestions.append("Make sure the database file exists and is accessible.")
        code_examples.append("autoresearch config init --force")
    
    elif isinstance(exception, SearchError):
        suggestions.append("Check your search configuration.")
        if "timeout" in str(exception).lower():
            suggestions.append("Try again later or check your internet connection.")
    
    elif isinstance(exception, TimeoutError):
        severity = ErrorSeverity.WARNING
        suggestions.append("The operation timed out. Try again later.")
        if "timeout" in context:
            suggestions.append(f"Consider increasing the timeout value (current: {context['timeout']}).")
    
    elif isinstance(exception, NotFoundError):
        if "resource_type" in context and "resource_id" in context:
            suggestions.append(f"The {context['resource_type']} with ID {context['resource_id']} was not found.")
    
    elif isinstance(exception, BackupError):
        if "suggestion" in context:
            suggestions.append(context["suggestion"])
    
    # Log the error
    logger.error(f"Error: {message}", exc_info=exception)
    
    return ErrorInfo(
        message=message,
        severity=severity,
        exception=exception,
        suggestions=suggestions,
        code_examples=code_examples,
        context=context,
    )

def format_error_for_cli(error_info: ErrorInfo) -> Tuple[str, Optional[str], Optional[str]]:
    """Format error information for CLI output.
    
    Args:
        error_info: The error information to format
        
    Returns:
        A tuple containing the error message, suggestion, and code example
    """
    message = error_info.message
    suggestion = None
    code_example = None
    
    if error_info.suggestions:
        suggestion = error_info.suggestions[0]
    
    if error_info.code_examples:
        code_example = error_info.code_examples[0]
    
    return message, suggestion, code_example

def format_error_for_gui(error_info: ErrorInfo) -> str:
    """Format error information for GUI output.
    
    Args:
        error_info: The error information to format
        
    Returns:
        A formatted error message for GUI display
    """
    parts = [error_info.message]
    
    if error_info.suggestions:
        parts.append("\n\nSuggestions:")
        for suggestion in error_info.suggestions:
            parts.append(f"• {suggestion}")
    
    if error_info.code_examples:
        parts.append("\n\nExamples:")
        for example in error_info.code_examples:
            parts.append(f"`{example}`")
    
    return "\n".join(parts)

def format_error_for_api(error_info: ErrorInfo) -> Dict[str, Any]:
    """Format error information for API output.
    
    Args:
        error_info: The error information to format
        
    Returns:
        A dictionary containing the formatted error information
    """
    return {
        "error": error_info.message,
        "severity": error_info.severity,
        "suggestions": error_info.suggestions,
        "code_examples": error_info.code_examples,
        "context": error_info.context,
    }

def format_error_for_a2a(error_info: ErrorInfo) -> Dict[str, Any]:
    """Format error information for A2A output.
    
    Args:
        error_info: The error information to format
        
    Returns:
        A dictionary containing the formatted error information
    """
    return {
        "status": "error",
        "error": error_info.message,
        "suggestions": error_info.suggestions,
        "code_examples": error_info.code_examples,
    }