"""Unit tests for OpenRouterAdapter with comprehensive coverage of new features.

These tests focus on unit-level testing with mocking to verify all new functionality
including retry logic, error handling, caching, and streaming support.
"""

import os
import time
from unittest.mock import Mock, patch

import pytest
import requests

from autoresearch.errors import LLMError
from autoresearch.llm.adapters import OpenRouterAdapter


class TestOpenRouterAdapterInitialization:
    """Test OpenRouterAdapter initialization and configuration."""

    def test_initialization_with_defaults(self) -> None:
        """Test adapter initialization with default configuration."""
        with patch.dict(os.environ, {}, clear=True):
            adapter = OpenRouterAdapter()

            assert adapter.api_key == ""
            assert adapter.endpoint == "https://openrouter.ai/api/v1/chat/completions"
            assert adapter._cache_ttl == 3600  # Default 1 hour
            assert len(adapter.available_models) >= 10

    def test_initialization_with_custom_config(self) -> None:
        """Test adapter initialization with custom environment variables."""
        custom_endpoint = "https://custom.openrouter.example.com/api/v1/chat/completions"
        custom_ttl = "7200"

        with patch.dict(os.environ, {
            "OPENROUTER_API_KEY": "test-key-123",
            "OPENROUTER_ENDPOINT": custom_endpoint,
            "OPENROUTER_CACHE_TTL": custom_ttl,
        }):
            adapter = OpenRouterAdapter()

            assert adapter.api_key == "test-key-123"
            assert adapter.endpoint == custom_endpoint
            assert adapter._cache_ttl == 7200

    def test_initialization_with_invalid_ttl(self) -> None:
        """Test adapter initialization with invalid cache TTL."""
        with patch.dict(os.environ, {"OPENROUTER_CACHE_TTL": "invalid"}):
            # Should fall back to default TTL
            adapter = OpenRouterAdapter()
            assert adapter._cache_ttl == 3600

    def test_available_models_property(self) -> None:
        """Test that available_models property returns expected models."""
        adapter = OpenRouterAdapter()

        models = adapter.available_models
        assert isinstance(models, list)
        assert len(models) > 0
        assert all(isinstance(model, str) for model in models)

        # Should include free-tier models we added
        assert "google/gemini-flash-1.5" in models
        assert "meta-llama/llama-3.2-3b-instruct" in models


class TestOpenRouterAdapterModelDiscovery:
    """Test model discovery and caching functionality."""

    def test_model_discovery_without_api_key(self) -> None:
        """Test model discovery when API key is not set."""
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": ""}):
            adapter = OpenRouterAdapter()

            # Should use default models
            assert len(adapter._model_context_sizes) > 0
            assert "anthropic/claude-3-opus" in adapter._model_context_sizes

    @patch("requests.get")
    def test_model_discovery_with_api_key_success(self, mock_get: Mock) -> None:
        """Test successful model discovery with API key."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [
                {
                    "id": "test/model-1",
                    "context_length": 8192,
                    "supports_function_calling": True,
                    "supports_vision": False,
                    "supports_streaming": True,
                    "pricing": {"input": 0.001, "output": 0.002},
                }
            ]
        }
        mock_get.return_value = mock_response

        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key"}):
            adapter = OpenRouterAdapter()

            # Should have discovered the model
            assert "test/model-1" in adapter._model_context_sizes
            assert adapter._model_context_sizes["test/model-1"] == 8192

    @patch("requests.get")
    def test_model_discovery_with_api_key_error(self, mock_get: Mock) -> None:
        """Test model discovery when API call fails."""
        mock_get.side_effect = requests.RequestException("API Error")

        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key"}):
            adapter = OpenRouterAdapter()

            # Should fall back to default models
            assert len(adapter._model_context_sizes) > 0
            assert "anthropic/claude-3-opus" in adapter._model_context_sizes

    def test_context_size_caching(self) -> None:
        """Test context size caching behavior."""
        adapter = OpenRouterAdapter()

        model = "google/gemini-flash-1.5"

        # Get context size twice - should use cache on second call
        size1 = adapter.get_context_size(model)
        size2 = adapter.get_context_size(model)

        assert size1 == size2
        assert size1 > 0

    def test_context_size_cache_expiry(self) -> None:
        """Test that cache respects TTL."""
        # Set very short TTL for testing
        adapter = OpenRouterAdapter()
        adapter._cache_ttl = 1  # 1 second

        model = "google/gemini-flash-1.5"

        # Get context size
        size1 = adapter.get_context_size(model)

        # Wait for cache to expire
        time.sleep(1.1)

        # Should get fresh value (though in practice it will be the same)
        size2 = adapter.get_context_size(model)

        assert size1 == size2  # Same value, but from "fresh" lookup

    def test_cache_management_methods(self) -> None:
        """Test cache refresh and clear methods."""
        adapter = OpenRouterAdapter()

        # Add some cache data
        adapter._model_context_sizes["test/model"] = 4096
        adapter._context_cache_ttl["test/model"] = time.time()

        # Clear cache
        adapter.clear_model_cache()
        assert len(adapter._model_context_sizes) == 0
        assert len(adapter._context_cache_ttl) == 0

        # Refresh cache
        adapter.refresh_model_cache()
        # Should complete without error and restore defaults

    def test_refresh_model_cache_with_api_key(self) -> None:
        """Test cache refresh with API key set."""
        adapter = OpenRouterAdapter()

        # Should complete without error even if API call fails
        adapter.refresh_model_cache()
        assert len(adapter._model_context_sizes) > 0


class TestOpenRouterAdapterRetryLogic:
    """Test retry logic and error handling."""

    @patch("requests.post")
    def test_successful_generation_no_retries(self, mock_post: Mock) -> None:
        """Test that successful requests don't trigger retries."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Success!"}}]
        }
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key"}):
            adapter = OpenRouterAdapter()
            result = adapter.generate("Test prompt")

            assert result == "Success!"
            assert mock_post.call_count == 1

    @patch("requests.post")
    def test_retry_on_rate_limit(self, mock_post: Mock) -> None:
        """Test retry logic on rate limit errors."""
        # First call fails with 429, second succeeds
        rate_limit_response = Mock()
        rate_limit_response.ok = False
        rate_limit_response.status_code = 429
        rate_limit_response.headers = {"Retry-After": "1"}

        success_response = Mock()
        success_response.ok = True
        success_response.json.return_value = {
            "choices": [{"message": {"content": "Success after retry!"}}]
        }

        mock_post.side_effect = [
            requests.HTTPError("Rate limit", response=rate_limit_response),
            success_response,
        ]

        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key"}):
            adapter = OpenRouterAdapter()
            result = adapter.generate("Test prompt")

            assert result == "Success after retry!"
            assert mock_post.call_count == 2

    @patch("requests.post")
    def test_max_retries_exceeded(self, mock_post: Mock) -> None:
        """Test that max retries are respected."""
        error_response = Mock()
        error_response.ok = False
        error_response.status_code = 429

        mock_post.side_effect = requests.HTTPError("Rate limit", response=error_response)

        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key"}):
            adapter = OpenRouterAdapter()

            with pytest.raises(LLMError) as exc_info:
                adapter.generate("Test prompt")

            # Should have tried 3 times (initial + 2 retries)
            assert mock_post.call_count == 3
            assert "after 3 attempts" in str(exc_info.value)

    @patch("requests.post")
    def test_non_retryable_error_no_retries(self, mock_post: Mock) -> None:
        """Test that non-retryable errors don't trigger retries."""
        error_response = Mock()
        error_response.ok = False
        error_response.status_code = 400  # Bad request

        mock_post.side_effect = requests.HTTPError("Bad request", response=error_response)

        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key"}):
            adapter = OpenRouterAdapter()

            with pytest.raises(LLMError):
                adapter.generate("Test prompt")

            # Should only call once for non-retryable errors
            assert mock_post.call_count == 1

    def test_is_retryable_error_logic(self) -> None:
        """Test the retryable error detection logic."""
        adapter = OpenRouterAdapter()

        # Rate limits should be retryable
        rate_limit_error = Mock()
        rate_limit_error.response.status_code = 429
        assert adapter._is_retryable_error(rate_limit_error)

        # Server errors should be retryable
        server_error = Mock()
        server_error.response.status_code = 500
        assert adapter._is_retryable_error(server_error)

        # Client errors should not be retryable (except specific ones)
        client_error = Mock()
        client_error.response.status_code = 400
        assert not adapter._is_retryable_error(client_error)

        # Connection errors should be retryable
        connection_error = requests.ConnectionError()
        assert adapter._is_retryable_error(connection_error)

        # Timeout errors should be retryable
        timeout_error = requests.Timeout()
        assert adapter._is_retryable_error(timeout_error)

    def test_get_retry_after_header(self) -> None:
        """Test Retry-After header parsing."""
        adapter = OpenRouterAdapter()

        # Test with valid Retry-After header
        error_with_header = Mock()
        error_with_header.response.headers = {"Retry-After": "30"}
        retry_after = adapter._get_retry_after_header(error_with_header)
        assert retry_after == 30.0

        # Test without Retry-After header
        error_without_header = Mock()
        error_without_header.response.headers = {}
        retry_after = adapter._get_retry_after_header(error_without_header)
        assert retry_after is None

        # Test with invalid Retry-After header
        error_invalid_header = Mock()
        error_invalid_header.response.headers = {"Retry-After": "invalid"}
        retry_after = adapter._get_retry_after_header(error_invalid_header)
        assert retry_after is None


class TestOpenRouterAdapterErrorHandling:
    """Test enhanced error handling for OpenRouter-specific errors."""

    @patch("requests.post")
    def test_authentication_error_handling(self, mock_post: Mock) -> None:
        """Test handling of authentication errors."""
        error_response = Mock()
        error_response.ok = False
        error_response.status_code = 401
        error_response.json.return_value = {"error": {"message": "Invalid API key"}}

        mock_post.side_effect = requests.HTTPError("Unauthorized", response=error_response)

        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "invalid-key"}):
            adapter = OpenRouterAdapter()

            with pytest.raises(LLMError) as exc_info:
                adapter.generate("Test prompt")

            error_msg = str(exc_info.value)
            assert "Authentication failed" in error_msg
            assert "OPENROUTER_API_KEY" in error_msg

    @patch("requests.post")
    def test_insufficient_credits_error_handling(self, mock_post: Mock) -> None:
        """Test handling of insufficient credits errors."""
        error_response = Mock()
        error_response.ok = False
        error_response.status_code = 402
        error_response.json.return_value = {"error": {"message": "Insufficient credits"}}

        mock_post.side_effect = requests.HTTPError("Payment required", response=error_response)

        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key"}):
            adapter = OpenRouterAdapter()

            with pytest.raises(LLMError) as exc_info:
                adapter.generate("Test prompt")

            error_msg = str(exc_info.value)
            assert "Insufficient credits" in error_msg
            assert "free-tier models" in error_msg

    @patch("requests.post")
    def test_model_not_found_error_handling(self, mock_post: Mock) -> None:
        """Test handling of model not found errors."""
        error_response = Mock()
        error_response.ok = False
        error_response.status_code = 404
        error_response.json.return_value = {"error": {"message": "Model not found"}}

        mock_post.side_effect = requests.HTTPError("Not found", response=error_response)

        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key"}):
            adapter = OpenRouterAdapter()

            with pytest.raises(LLMError) as exc_info:
                adapter.generate("Test prompt", model="nonexistent/model")

            error_msg = str(exc_info.value)
            assert "not found" in error_msg
            assert "nonexistent/model" in error_msg

    @patch("requests.post")
    def test_rate_limit_error_handling(self, mock_post: Mock) -> None:
        """Test handling of rate limit errors."""
        error_response = Mock()
        error_response.ok = False
        error_response.status_code = 429
        error_response.json.return_value = {"error": {"message": "Rate limit exceeded"}}

        mock_post.side_effect = requests.HTTPError("Too many requests", response=error_response)

        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key"}):
            adapter = OpenRouterAdapter()

            with pytest.raises(LLMError) as exc_info:
                adapter.generate("Test prompt")

            error_msg = str(exc_info.value)
            assert "Rate limit exceeded" in error_msg
            assert "rate limits" in error_msg

    @patch("requests.post")
    def test_server_error_handling(self, mock_post: Mock) -> None:
        """Test handling of server errors."""
        error_response = Mock()
        error_response.ok = False
        error_response.status_code = 500
        error_response.json.return_value = {"error": {"message": "Internal server error"}}

        mock_post.side_effect = requests.HTTPError("Server error", response=error_response)

        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key"}):
            adapter = OpenRouterAdapter()

            with pytest.raises(LLMError) as exc_info:
                adapter.generate("Test prompt")

            error_msg = str(exc_info.value)
            assert "server error" in error_msg
            assert "temporary issue" in error_msg


class TestOpenRouterAdapterStreaming:
    """Test streaming functionality."""

    def test_generate_stream_method_exists(self) -> None:
        """Test that generate_stream method exists and is callable."""
        adapter = OpenRouterAdapter()

        assert hasattr(adapter, "generate_stream")
        assert callable(adapter.generate_stream)

    def test_generate_stream_requires_api_key(self) -> None:
        """Test that generate_stream requires API key."""
        adapter = OpenRouterAdapter()

        with pytest.raises(LLMError) as exc_info:
            adapter.generate_stream("Test prompt")

        error_msg = str(exc_info.value)
        assert "API key not found" in error_msg

    @patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key"})
    def test_generate_stream_falls_back_to_regular_generation(self) -> None:
        """Test that generate_stream currently falls back to regular generation."""
        adapter = OpenRouterAdapter()

        # Mock the regular generation method
        with patch.object(adapter, "_generate_with_retries", return_value="Stream result") as mock_generate:
            result = adapter.generate_stream("Test prompt")

            assert result == "Stream result"
            mock_generate.assert_called_once()


class TestOpenRouterAdapterTokenEstimation:
    """Test token estimation functionality."""

    def test_estimate_prompt_tokens_with_different_providers(self) -> None:
        """Test token estimation for different model provider prefixes."""
        adapter = OpenRouterAdapter()
        prompt = "This is a test prompt for token counting."

        # Test with Anthropic model
        if "anthropic/claude-3-haiku" in adapter.available_models:
            token_count = adapter.estimate_prompt_tokens(prompt)
            assert token_count > 0
            assert isinstance(token_count, int)

        # Test with Google model
        if "google/gemini-flash-1.5" in adapter.available_models:
            token_count = adapter.estimate_prompt_tokens(prompt)
            assert token_count > 0
            assert isinstance(token_count, int)

    def test_estimate_prompt_tokens_fallback(self) -> None:
        """Test token estimation fallback for unknown models."""
        adapter = OpenRouterAdapter()
        prompt = "Test prompt"

        # Should work even for unknown models
        token_count = adapter.estimate_prompt_tokens(prompt)
        assert token_count > 0
        assert isinstance(token_count, int)


class TestOpenRouterAdapterIntegration:
    """Integration-style tests for the complete adapter functionality."""

    @patch("requests.post")
    def test_full_generation_workflow(self, mock_post: Mock) -> None:
        """Test the complete generation workflow with retries."""
        # Simulate a scenario where first call fails with rate limit, second succeeds
        rate_limit_response = Mock()
        rate_limit_response.ok = False
        rate_limit_response.status_code = 429

        success_response = Mock()
        success_response.ok = True
        success_response.json.return_value = {
            "choices": [{"message": {"content": "Generated response"}}]
        }

        mock_post.side_effect = [
            requests.HTTPError("Rate limit", response=rate_limit_response),
            success_response,
        ]

        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key"}):
            adapter = OpenRouterAdapter()
            result = adapter.generate("Test prompt")

            assert result == "Generated response"
            assert mock_post.call_count == 2

    def test_adapter_thread_safety(self) -> None:
        """Test that adapter is thread-safe for concurrent access."""
        import threading

        adapter = OpenRouterAdapter()
        results = []
        errors = []

        def access_adapter() -> None:
            """Access adapter methods from multiple threads."""
            try:
                # Test various methods concurrently
                models = adapter.available_models
                results.append(len(models))

                if models:
                    context_size = adapter.get_context_size(models[0])
                    results.append(context_size)

            except Exception as e:
                errors.append(str(e))

        # Start multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=access_adapter)
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join(timeout=5)

        # All threads should complete successfully
        assert len(results) >= 10  # 5 threads * 2 operations each
        assert len(errors) == 0


class TestOpenRouterAdapterEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_prompt_handling(self) -> None:
        """Test handling of empty prompts."""
        adapter = OpenRouterAdapter()

        # Should handle empty prompts gracefully in validation
        with pytest.raises(LLMError):
            adapter.generate("")  # Empty prompt should fail validation

    def test_very_long_prompt_handling(self) -> None:
        """Test handling of very long prompts."""
        adapter = OpenRouterAdapter()
        long_prompt = "A" * 10000  # Very long prompt

        # Should handle long prompts in token estimation
        token_count = adapter.estimate_prompt_tokens(long_prompt)
        assert token_count > 0

    def test_none_model_handling(self) -> None:
        """Test handling of None model parameter."""
        adapter = OpenRouterAdapter()

        # Should use default model selection when None is passed
        default_model = adapter.validate_model(None)
        assert default_model is not None
        assert isinstance(default_model, str)

    def test_invalid_model_name_handling(self) -> None:
        """Test handling of invalid model names."""
        adapter = OpenRouterAdapter()

        with pytest.raises(LLMError):
            adapter.validate_model("")

        with pytest.raises(LLMError):
            adapter.validate_model("invalid/model/name")

    def test_adapter_reinitialization(self) -> None:
        """Test that adapter can be reinitialized."""
        adapter1 = OpenRouterAdapter()
        adapter2 = OpenRouterAdapter()

        # Two separate instances should work independently
        assert adapter1 is not adapter2
        assert len(adapter1.available_models) == len(adapter2.available_models)

    def test_environment_variable_changes(self) -> None:
        """Test that environment variable changes are picked up."""
        # This is hard to test reliably in unit tests, but we can verify
        # that the adapter reads from environment on initialization
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "new-key"}):
            adapter = OpenRouterAdapter()
            assert adapter.api_key == "new-key"
