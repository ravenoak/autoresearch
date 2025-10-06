# mypy: ignore-errors
from autoresearch.errors import (
    AgentError,
    AutoresearchError,
    ConfigError,
    LLMError,
    NotFoundError,
    OrchestrationError,
    SearchError,
    StorageError,
    TimeoutError,
    ValidationError,
)


def test_error_hierarchy() -> None:
    """Test that all errors inherit from AutoresearchError."""
    assert issubclass(ConfigError, AutoresearchError)
    assert issubclass(AgentError, AutoresearchError)
    assert issubclass(LLMError, AutoresearchError)
    assert issubclass(StorageError, AutoresearchError)
    assert issubclass(SearchError, AutoresearchError)
    assert issubclass(OrchestrationError, AutoresearchError)
    assert issubclass(ValidationError, AutoresearchError)
    assert issubclass(TimeoutError, AutoresearchError)
    assert issubclass(NotFoundError, AutoresearchError)


def test_error_messages() -> None:
    """Test that error messages are properly formatted."""
    error = AutoresearchError("Test message")
    assert str(error) == "Test message"

    error = ConfigError("Invalid config")
    assert str(error) == "Invalid config"

    error = AgentError("Agent failed", agent_name="TestAgent")
    assert str(error) == "Agent failed (agent: TestAgent)"

    error = LLMError("LLM request failed", model="gpt-3.5-turbo")
    assert str(error) == "LLM request failed (model: gpt-3.5-turbo)"


def test_error_with_cause() -> None:
    """Test that errors can be created with a cause."""
    cause = ValueError("Original error")
    error = AutoresearchError("Wrapped error", cause=cause)
    assert str(error) == "Wrapped error"
    assert error.__cause__ == cause


def test_timeout_error() -> None:
    """Test the TimeoutError class."""
    error = TimeoutError("Operation timed out", timeout=30)
    assert str(error) == "Operation timed out (timeout: 30s)"


def test_not_found_error() -> None:
    """Test the NotFoundError class."""
    error = NotFoundError("Resource not found", resource_type="User", resource_id="123")
    assert str(error) == "Resource not found (resource_type: User, resource_id: 123)"
