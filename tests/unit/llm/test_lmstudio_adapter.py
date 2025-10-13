"""Regression tests for the LM Studio adapter."""

from __future__ import annotations

from typing import Any

import pytest
import requests
from requests import Response
from requests.exceptions import HTTPError

from autoresearch.errors import LLMError
from autoresearch.llm.adapters import LMStudioAdapter


class _DummySession:
    """Simple stand-in for a requests session."""

    def __init__(self, side_effect: Exception | None = None, payload: str | None = None) -> None:
        self.side_effect = side_effect
        self.payload = payload or "Hello from LM Studio"

    def post(self, endpoint: str, json: dict[str, Any], timeout: float) -> Response:
        if self.side_effect:
            raise self.side_effect
        response = Response()
        response.status_code = 200
        response._content = (  # type: ignore[attr-defined]
            f'{{"choices": [{{"message": {{"content": "{self.payload}"}}}}]}}'.encode("utf-8")
        )
        return response

    def get(self, endpoint: str, timeout: float) -> Response:
        """Mock GET request for model discovery."""
        # For model discovery, return a successful response with some test models
        response = Response()
        response.status_code = 200
        response._content = (  # type: ignore[attr-defined]
            '{"data": [{"id": "test-model-1"}, {"id": "test-model-2"}]}'.encode("utf-8")
        )
        return response


def test_lmstudio_adapter_passes_through_model_identifier() -> None:
    """Model identifiers should not be restricted to the static allowlist."""

    adapter = LMStudioAdapter()
    assert adapter.validate_model("qwen/qwen3-4b-2507") == "qwen/qwen3-4b-2507"


def test_lmstudio_adapter_timeout_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Timeout should be configurable via environment variables with graceful fallback."""

    monkeypatch.setenv("LMSTUDIO_TIMEOUT", "42.5")
    adapter = LMStudioAdapter()
    assert pytest.approx(getattr(adapter, "timeout")) == 42.5

    monkeypatch.setenv("LMSTUDIO_TIMEOUT", "invalid")
    adapter = LMStudioAdapter()
    assert pytest.approx(getattr(adapter, "timeout")) == 300.0


def test_lmstudio_adapter_http_error_surfaces_metadata(monkeypatch: pytest.MonkeyPatch) -> None:
    """HTTP errors should be wrapped with actionable metadata for diagnostics."""

    response = Response()
    response.status_code = 400
    response._content = b"Bad Request"  # type: ignore[attr-defined]
    error = HTTPError("bad request")
    error.response = response
    monkeypatch.setattr(
        "autoresearch.llm.adapters.get_session",
        lambda: _DummySession(side_effect=error),
    )

    adapter = LMStudioAdapter()
    with pytest.raises(LLMError) as excinfo:
        adapter.generate("test prompt", model="qwen/qwen3-4b-2507")

    err = excinfo.value
    assert err.context["metadata"]["status_code"] == 400
    assert "Inspect LM Studio server logs" in err.context["suggestion"]


def test_lmstudio_adapter_request_exception_has_default_suggestion(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Non-HTTP request failures should fall back to the connectivity hint."""

    monkeypatch.setattr(
        "autoresearch.llm.adapters.get_session",
        lambda: _DummySession(
            side_effect=requests.exceptions.ConnectionError("disconnected")
        ),
    )

    adapter = LMStudioAdapter()
    with pytest.raises(LLMError) as excinfo:
        adapter.generate("prompt")

    assert "Ensure LM Studio is running" in excinfo.value.context["suggestion"]


def test_lmstudio_adapter_model_discovery_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Model discovery should successfully retrieve models from LM Studio API."""

    # Mock the _discover_available_models method directly to avoid session mocking issues
    def mock_discover(self):
        self._discovered_models = ["llama-2-7b-chat", "codellama-13b-instruct", "mistral-7b-instruct"]
        self._model_discovery_error = None

    monkeypatch.setattr(
        "autoresearch.llm.adapters.LMStudioAdapter._discover_available_models",
        mock_discover,
    )

    adapter = LMStudioAdapter()

    # Check that models were discovered
    model_info = adapter.get_model_info()
    assert model_info["using_discovered"] is True
    assert len(model_info["discovered_models"]) == 3
    assert "llama-2-7b-chat" in model_info["discovered_models"]
    assert "codellama-13b-instruct" in model_info["discovered_models"]
    assert "mistral-7b-instruct" in model_info["discovered_models"]

    # Check that discovered models are used for validation
    available = adapter.available_models
    assert len(available) == 3
    assert available == model_info["discovered_models"]


def test_lmstudio_adapter_model_discovery_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """Model discovery failure should fall back to default models."""

    class _FailedDiscoverySession(_DummySession):
        def get(self, endpoint: str, timeout: float) -> Response:
            # Simulate API failure
            raise requests.exceptions.ConnectionError("Connection failed")

    monkeypatch.setattr(
        "autoresearch.llm.adapters.get_session",
        lambda: _FailedDiscoverySession(),
    )

    adapter = LMStudioAdapter()

    # Check that discovery failed but fallback was used
    model_info = adapter.get_model_info()
    assert model_info["using_discovered"] is False
    assert model_info["discovery_error"] is not None
    assert "Failed to discover models from LM Studio" in model_info["discovery_error"]

    # Check that fallback models are used
    available = adapter.available_models
    expected_fallbacks = ["lmstudio", "llama2", "mistral", "mixtral"]
    assert available == expected_fallbacks


def test_lmstudio_adapter_model_discovery_empty_response(monkeypatch: pytest.MonkeyPatch) -> None:
    """Model discovery with empty response should fall back to default models."""

    class _EmptyDiscoverySession(_DummySession):
        def get(self, endpoint: str, timeout: float) -> Response:
            response = Response()
            response.status_code = 200
            response._content = '{"data": []}'.encode("utf-8")  # Empty model list
            return response

    monkeypatch.setattr(
        "autoresearch.llm.adapters.get_session",
        lambda: _EmptyDiscoverySession(),
    )

    adapter = LMStudioAdapter()

    # Check that discovery failed due to empty response
    model_info = adapter.get_model_info()
    assert model_info["using_discovered"] is False
    assert "No models found in LM Studio API response" in model_info["discovery_error"]

    # Check that fallback models are used
    available = adapter.available_models
    expected_fallbacks = ["lmstudio", "llama2", "mistral", "mixtral"]
    assert available == expected_fallbacks


def test_lmstudio_adapter_model_discovery_malformed_response(monkeypatch: pytest.MonkeyPatch) -> None:
    """Model discovery with malformed response should fall back to default models."""

    class _MalformedDiscoverySession(_DummySession):
        def get(self, endpoint: str, timeout: float) -> Response:
            response = Response()
            response.status_code = 200
            response._content = '{"invalid": "response"}'.encode("utf-8")  # Malformed JSON
            return response

    monkeypatch.setattr(
        "autoresearch.llm.adapters.get_session",
        lambda: _MalformedDiscoverySession(),
    )

    adapter = LMStudioAdapter()

    # Check that discovery failed due to malformed response
    model_info = adapter.get_model_info()
    assert model_info["using_discovered"] is False
    assert model_info["discovery_error"] is not None

    # Check that fallback models are used
    available = adapter.available_models
    expected_fallbacks = ["lmstudio", "llama2", "mistral", "mixtral"]
    assert available == expected_fallbacks


def test_lmstudio_adapter_model_validation_with_discovered_models(monkeypatch: pytest.MonkeyPatch) -> None:
    """Model validation should work with discovered models."""

    # Mock the _discover_available_models method directly
    def mock_discover(self):
        self._discovered_models = ["llama-2-7b-chat", "codellama-13b-instruct"]
        self._model_discovery_error = None

    monkeypatch.setattr(
        "autoresearch.llm.adapters.LMStudioAdapter._discover_available_models",
        mock_discover,
    )

    adapter = LMStudioAdapter()

    # Test validation with discovered model
    validated = adapter.validate_model("llama-2-7b-chat")
    assert validated == "llama-2-7b-chat"

    # Test validation with None (should use first discovered model)
    validated_default = adapter.validate_model(None)
    assert validated_default == "llama-2-7b-chat"

    # Test validation with fallback model when discovered models exist
    validated_fallback = adapter.validate_model("mistral")
    assert validated_fallback == "mistral"


def test_lmstudio_adapter_model_info_comprehensive(monkeypatch: pytest.MonkeyPatch) -> None:
    """Model info should provide comprehensive information about discovery status."""

    # Mock the _discover_available_models method directly
    def mock_discover(self):
        self._discovered_models = ["test-model-1", "test-model-2"]
        self._model_discovery_error = None

    monkeypatch.setattr(
        "autoresearch.llm.adapters.LMStudioAdapter._discover_available_models",
        mock_discover,
    )

    adapter = LMStudioAdapter()
    model_info = adapter.get_model_info()

    # Check all expected keys are present
    expected_keys = [
        "discovered_models",
        "fallback_models",
        "discovery_error",
        "endpoint",
        "using_discovered"
    ]
    for key in expected_keys:
        assert key in model_info

    # Check specific values
    assert model_info["using_discovered"] is True
    assert len(model_info["discovered_models"]) == 2
    assert model_info["discovery_error"] is None
    assert model_info["endpoint"] == "http://localhost:1234/v1/chat/completions"
    assert model_info["fallback_models"] == ["lmstudio", "llama2", "mistral", "mixtral"]


def test_lmstudio_adapter_context_size_estimation(monkeypatch: pytest.MonkeyPatch) -> None:
    """Context size estimation should work for various model types."""

    # Mock the _discover_available_models method to set up context sizes
    def mock_discover(self):
        self._discovered_models = ["qwen3-4b", "deepseek-8b", "mistral-7b"]
        self._model_context_sizes = {
            "qwen3-4b": 8192,
            "deepseek-8b": 16384,
            "mistral-7b": 4096,
        }
        self._model_discovery_error = None

    monkeypatch.setattr(
        "autoresearch.llm.adapters.LMStudioAdapter._discover_available_models",
        mock_discover,
    )

    adapter = LMStudioAdapter()

    # Test context size estimation for different models
    assert adapter.get_context_size("qwen3-4b") == 8192
    assert adapter.get_context_size("deepseek-8b") == 16384
    assert adapter.get_context_size("mistral-7b") == 4096

    # Test fallback for unknown models
    assert adapter.get_context_size("unknown-model") == 4096


def test_lmstudio_adapter_token_estimation() -> None:
    """Token estimation should provide reasonable approximations."""

    adapter = LMStudioAdapter()

    # Test token estimation for different text lengths
    short_text = "Hello world"
    assert adapter.estimate_prompt_tokens(short_text) == 2  # len("Hello world") // 4 = 11 // 4 = 2

    medium_text = "This is a longer text that should estimate to more tokens for testing purposes."
    estimated = adapter.estimate_prompt_tokens(medium_text)
    assert estimated > 5  # Should be more than short text

    long_text = "A" * 1000  # 1000 characters
    estimated = adapter.estimate_prompt_tokens(long_text)
    assert estimated == 250  # 1000 // 4 = 250


def test_lmstudio_adapter_context_fit_checking(monkeypatch: pytest.MonkeyPatch) -> None:
    """Context fit checking should accurately assess prompt compatibility."""

    # Mock the _discover_available_models method
    def mock_discover(self):
        self._discovered_models = ["small-model", "large-model"]
        self._model_context_sizes = {
            "small-model": 2048,
            "large-model": 16384,
        }
        self._model_discovery_error = None

    monkeypatch.setattr(
        "autoresearch.llm.adapters.LMStudioAdapter._discover_available_models",
        mock_discover,
    )

    adapter = LMStudioAdapter()

    # Test fitting prompt
    fits, warning = adapter.check_context_fit("Short prompt", "small-model")
    assert fits is True
    assert warning is None

    # Test non-fitting prompt
    long_prompt = "A" * 10000  # Very long prompt
    fits, warning = adapter.check_context_fit(long_prompt, "small-model")
    assert fits is False
    assert warning is not None
    assert "exceeds available context" in warning


def test_lmstudio_adapter_intelligent_truncation(monkeypatch: pytest.MonkeyPatch) -> None:
    """Intelligent truncation should preserve sentence boundaries when possible."""

    # Mock the _discover_available_models method
    def mock_discover(self):
        self._discovered_models = ["test-model"]
        self._model_context_sizes = {"test-model": 10}  # Very small context for testing (30 chars max)
        self._model_discovery_error = None

    monkeypatch.setattr(
        "autoresearch.llm.adapters.LMStudioAdapter._discover_available_models",
        mock_discover,
    )

    adapter = LMStudioAdapter()

    # Test truncation of a multi-sentence prompt
    prompt = "First sentence. Second sentence that is longer. Third sentence."
    truncated = adapter.truncate_prompt(prompt, "test-model")

    assert len(truncated) < len(prompt)  # Should be truncated
    assert "... [content truncated to fit context]" in truncated  # Should have truncation marker
    assert "First sentence." in truncated  # Should preserve complete sentences


def test_lmstudio_adapter_adaptive_token_budgeting(monkeypatch: pytest.MonkeyPatch) -> None:
    """Adaptive token budgeting should adjust based on model capabilities."""

    # Mock the _discover_available_models method
    def mock_discover(self):
        self._discovered_models = ["small-model", "large-model"]
        self._model_context_sizes = {
            "small-model": 4096,
            "large-model": 16384,
        }
        self._model_discovery_error = None

    monkeypatch.setattr(
        "autoresearch.llm.adapters.LMStudioAdapter._discover_available_models",
        mock_discover,
    )

    adapter = LMStudioAdapter()

    # Test adaptive budgeting for different models
    small_budget = adapter.get_adaptive_token_budget("small-model")
    large_budget = adapter.get_adaptive_token_budget("large-model")

    assert small_budget < large_budget  # Large model should get higher budget
    assert small_budget > 1024  # Should be above minimum
    assert large_budget < 16384 - 512  # Should be below context size minus reserve


def test_lmstudio_adapter_usage_recording(monkeypatch: pytest.MonkeyPatch) -> None:
    """Usage recording should track performance metrics correctly."""

    # Mock the _discover_available_models method
    def mock_discover(self):
        self._discovered_models = ["test-model"]
        self._model_context_sizes = {"test-model": 4096}
        self._model_discovery_error = None

    monkeypatch.setattr(
        "autoresearch.llm.adapters.LMStudioAdapter._discover_available_models",
        mock_discover,
    )

    adapter = LMStudioAdapter()

    # Record some usage
    adapter.record_token_usage("test-model", 100, 200, success=True)
    adapter.record_token_usage("test-model", 150, 250, success=True)
    adapter.record_token_usage("test-model", 50, 0, success=False)  # Failed request

    # Check performance metrics
    metrics = adapter._performance_metrics["test-model"]
    assert metrics["total_count"] == 3
    assert metrics["success_count"] == 2
    assert metrics["total_tokens"] == 100 + 200 + 150 + 250 + 50 + 0  # 750

    # Check usage history
    history = adapter._token_usage_history["test-model"]
    assert len(history) == 3
    assert history == [300, 400, 50]  # prompt + response tokens


def test_lmstudio_adapter_context_size_suggestions(monkeypatch: pytest.MonkeyPatch) -> None:
    """Context size error suggestions should provide actionable advice."""

    # Mock the _discover_available_models method
    def mock_discover(self):
        self._discovered_models = ["small-model", "large-model"]
        self._model_context_sizes = {
            "small-model": 4096,
            "large-model": 8192,
        }
        self._model_discovery_error = None

    monkeypatch.setattr(
        "autoresearch.llm.adapters.LMStudioAdapter._discover_available_models",
        mock_discover,
    )

    adapter = LMStudioAdapter()

    # Test suggestion generation for context size error
    suggestion = adapter._generate_context_size_suggestion("small-model", 4096, 5000)

    assert "truncat" in suggestion.lower()  # Should suggest truncation
    assert "model with larger context window" in suggestion
    assert "large-model" in suggestion  # Should suggest the larger model


def test_lmstudio_adapter_context_aware_generation(monkeypatch: pytest.MonkeyPatch) -> None:
    """Generation should be context-aware and handle truncation gracefully."""

    # Mock successful model discovery
    def mock_discover(self):
        self._discovered_models = ["test-model"]
        self._model_context_sizes = {"test-model": 100}  # Very small for testing
        self._model_discovery_error = None

    monkeypatch.setattr(
        "autoresearch.llm.adapters.LMStudioAdapter._discover_available_models",
        mock_discover,
    )

    # Mock successful response
    class _SuccessSession(_DummySession):
        def post(self, endpoint: str, json: dict, timeout: float) -> Response:
            response = Response()
            response.status_code = 200
            response._content = '{"choices": [{"message": {"content": "Success response"}}]}'.encode("utf-8")
            return response

    monkeypatch.setattr(
        "autoresearch.llm.adapters.get_session",
        lambda: _SuccessSession(),
    )

    adapter = LMStudioAdapter()

    # Test generation with a long prompt that should be truncated
    long_prompt = "A" * 1000  # Long prompt that exceeds context
    response = adapter.generate(long_prompt, model="test-model")

    assert response == "Success response"  # Should still generate successfully


def test_lmstudio_adapter_enhanced_model_selection_integration(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test integration of enhanced model selection with LM Studio discovery."""

    # Mock LM Studio adapter to return specific models
    def mock_discover(self):
        self._discovered_models = ["qwen/qwen3-4b", "mistral-7b", "llama-2-7b"]
        self._model_context_sizes = {
            "qwen/qwen3-4b": 8192,
            "mistral-7b": 4096,
            "llama-2-7b": 4096,
        }
        self._model_discovery_error = None

    monkeypatch.setattr(
        "autoresearch.llm.adapters.LMStudioAdapter._discover_available_models",
        mock_discover,
    )

    # Test that discovered models are used in model selection
    adapter = LMStudioAdapter()
    model_info = adapter.get_model_info()

    # Verify discovery worked
    assert model_info["using_discovered"] is True
    assert len(model_info["discovered_models"]) == 3
    assert "qwen/qwen3-4b" in model_info["discovered_models"]

    # Test context size retrieval
    context_size = adapter.get_context_size("qwen/qwen3-4b")
    assert context_size == 8192

    # Test that largest context model is preferred in fallback
    # Create a mock config object
    class MockConfig:
        llm_backend = "lmstudio"

    fallback_model = adapter._get_intelligent_fallback(MockConfig(), "test-agent")
    assert fallback_model == "qwen/qwen3-4b"  # Should prefer largest context model


def test_lmstudio_adapter_model_discovery_fallback_behavior(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test fallback behavior when model discovery fails."""

    # Mock discovery failure
    def mock_discover_failed(self):
        self._discovered_models = []
        self._model_discovery_error = "Connection failed"
        self._fallback_to_heuristic_models()

    monkeypatch.setattr(
        "autoresearch.llm.adapters.LMStudioAdapter._discover_available_models",
        mock_discover_failed,
    )

    adapter = LMStudioAdapter()
    model_info = adapter.get_model_info()

    # Should not be using discovered models (they're fallbacks)
    assert model_info["using_discovered"] is False
    assert model_info["discovery_error"] == "Connection failed"

    # Should still have fallback models available
    available = adapter.available_models
    assert len(available) == 4  # lmstudio, llama2, mistral, mixtral
    assert "mistral" in available


def test_lmstudio_adapter_performance_tracking() -> None:
    """Test that performance metrics are tracked correctly."""

    adapter = LMStudioAdapter()

    # Record some usage
    adapter.record_token_usage("test-model", 100, 200, success=True)
    adapter.record_token_usage("test-model", 150, 250, success=True)
    adapter.record_token_usage("test-model", 50, 0, success=False)

    # Check performance metrics
    metrics = adapter._performance_metrics["test-model"]
    assert metrics["total_count"] == 3
    assert metrics["success_count"] == 2
    assert metrics["total_tokens"] == 750  # 100+200 + 150+250 + 50+0

    # Check usage history
    history = adapter._token_usage_history["test-model"]
    assert len(history) == 3
    assert history == [300, 400, 50]
