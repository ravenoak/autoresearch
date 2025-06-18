"""Unit tests for the LLM capabilities module.

This module tests the functionality of the LLM capability probing system,
including the ModelCapabilities class, CapabilityProber class, and helper functions.
"""

import os
from unittest.mock import patch, MagicMock
import responses

from autoresearch.llm.capabilities import (
    ModelCapabilities,
    CapabilityProber,
    get_capability_prober,
    probe_all_providers,
    get_model_capabilities,
)
from autoresearch.llm.registry import LLMFactory


class TestModelCapabilities:
    """Tests for the ModelCapabilities class."""

    def test_model_capabilities_creation(self):
        """Test creating a ModelCapabilities instance."""
        # Setup
        capabilities = ModelCapabilities(
            name="test-model",
            provider="test-provider",
            context_length=4096,
            supports_function_calling=True,
            supports_vision=False,
            supports_streaming=True,
            cost_per_1k_input_tokens=0.001,
            cost_per_1k_output_tokens=0.002,
        )

        # Verify
        assert capabilities.name == "test-model"
        assert capabilities.provider == "test-provider"
        assert capabilities.context_length == 4096
        assert capabilities.supports_function_calling is True
        assert capabilities.supports_vision is False
        assert capabilities.supports_streaming is True
        assert capabilities.cost_per_1k_input_tokens == 0.001
        assert capabilities.cost_per_1k_output_tokens == 0.002

    def test_to_dict_method(self):
        """Test the to_dict method of ModelCapabilities."""
        # Setup
        capabilities = ModelCapabilities(
            name="test-model",
            provider="test-provider",
            context_length=4096,
            supports_function_calling=True,
            supports_vision=False,
            supports_streaming=True,
            cost_per_1k_input_tokens=0.001,
            cost_per_1k_output_tokens=0.002,
        )

        # Execute
        result = capabilities.to_dict()

        # Verify
        assert isinstance(result, dict)
        assert result["name"] == "test-model"
        assert result["provider"] == "test-provider"
        assert result["context_length"] == 4096
        assert result["supports_function_calling"] is True
        assert result["supports_vision"] is False
        assert result["supports_streaming"] is True
        assert result["cost_per_1k_input_tokens"] == 0.001
        assert result["cost_per_1k_output_tokens"] == 0.002


class TestCapabilityProber:
    """Tests for the CapabilityProber class."""

    def test_singleton_pattern(self):
        """Test that CapabilityProber follows the singleton pattern."""
        # Execute
        prober1 = CapabilityProber.get_instance()
        prober2 = CapabilityProber.get_instance()

        # Verify
        assert prober1 is prober2

    def test_probe_provider_caching(self):
        """Test that probe_provider caches results."""
        # Setup
        prober = CapabilityProber.get_instance()

        # Clear the cache for testing
        prober._capabilities_cache = {}

        # Mock the _probe_dummy method
        with patch.object(prober, "_probe_dummy") as mock_probe:
            mock_probe.return_value = {
                "dummy": ModelCapabilities(
                    name="dummy",
                    provider="dummy",
                    context_length=1000,
                    supports_function_calling=False,
                    supports_vision=False,
                    supports_streaming=False,
                    cost_per_1k_input_tokens=0.0,
                    cost_per_1k_output_tokens=0.0,
                )
            }

            # Execute - first call should use the mock
            result1 = prober.probe_provider("dummy")

            # Execute - second call should use the cache
            result2 = prober.probe_provider("dummy")

        # Verify
        assert mock_probe.call_count == 1  # Method should only be called once
        assert result1 == result2  # Results should be identical
        assert "dummy" in prober._capabilities_cache  # Provider should be in cache

    def test_probe_provider_unknown(self):
        """Test probing an unknown provider."""
        # Setup
        prober = CapabilityProber.get_instance()

        # Execute
        result = prober.probe_provider("unknown_provider")

        # Verify
        assert result == {}

    @patch.object(LLMFactory, "_registry", {"openai": None, "dummy": None})
    def test_probe_all_providers(self):
        """Test probing all providers."""
        # Setup
        prober = CapabilityProber.get_instance()
        prober._capabilities_cache = {}
        prober._providers_probed = set()

        # Mock the probe_provider method
        with patch.object(prober, "probe_provider") as mock_probe:
            mock_probe.return_value = {}

            # Execute
            prober.probe_all_providers()

        # Verify
        assert mock_probe.call_count == 2  # Should be called for each provider
        mock_probe.assert_any_call("openai")
        mock_probe.assert_any_call("dummy")

    def test_get_model_capabilities_with_provider(self):
        """Test getting model capabilities with a specified provider."""
        # Setup
        prober = CapabilityProber.get_instance()

        # Create test data
        test_capabilities = ModelCapabilities(
            name="test-model",
            provider="test-provider",
            context_length=4096,
            supports_function_calling=True,
            supports_vision=False,
            supports_streaming=True,
            cost_per_1k_input_tokens=0.001,
            cost_per_1k_output_tokens=0.002,
        )

        # Set up the cache
        prober._capabilities_cache = {
            "test-provider": {"test-model": test_capabilities}
        }

        # Execute
        result = prober.get_model_capabilities("test-model", "test-provider")

        # Verify
        assert result == test_capabilities

    def test_get_model_capabilities_without_provider(self):
        """Test getting model capabilities without specifying a provider."""
        # Setup
        prober = CapabilityProber.get_instance()

        # Create test data
        test_capabilities = ModelCapabilities(
            name="test-model",
            provider="test-provider",
            context_length=4096,
            supports_function_calling=True,
            supports_vision=False,
            supports_streaming=True,
            cost_per_1k_input_tokens=0.001,
            cost_per_1k_output_tokens=0.002,
        )

        # Set up the cache
        prober._capabilities_cache = {
            "test-provider": {"test-model": test_capabilities}
        }

        # Execute
        result = prober.get_model_capabilities("test-model")

        # Verify
        assert result == test_capabilities

    def test_get_model_capabilities_not_found(self):
        """Test getting capabilities for a model that doesn't exist."""
        # Setup
        prober = CapabilityProber.get_instance()
        prober._capabilities_cache = {}

        # Execute
        result = prober.get_model_capabilities("nonexistent-model")

        # Verify
        assert result is None

    def test_get_model_capabilities_search_across_providers(self):
        """Test getting model capabilities by searching across all providers."""
        # Setup
        prober = CapabilityProber.get_instance()

        # Create test data
        test_capabilities = ModelCapabilities(
            name="test-model",
            provider="provider1",
            context_length=4096,
            supports_function_calling=True,
            supports_vision=False,
            supports_streaming=True,
            cost_per_1k_input_tokens=0.001,
            cost_per_1k_output_tokens=0.002,
        )

        # Set up the cache with multiple providers
        prober._capabilities_cache = {
            "provider1": {
                "other-model": ModelCapabilities(
                    name="other-model",
                    provider="provider1",
                    context_length=2048,
                    supports_function_calling=False,
                    supports_vision=False,
                    supports_streaming=True,
                    cost_per_1k_input_tokens=0.0005,
                    cost_per_1k_output_tokens=0.001,
                )
            },
            "provider2": {"test-model": test_capabilities},
        }

        # Execute
        result = prober.get_model_capabilities("test-model")

        # Verify
        assert result == test_capabilities

    @responses.activate
    def test_probe_openrouter_with_api(self):
        """Test probing OpenRouter capabilities using the API."""
        # Setup
        prober = CapabilityProber.get_instance()

        # Mock environment variable
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-api-key"}):
            # Mock API response
            responses.add(
                responses.GET,
                "https://openrouter.ai/api/v1/models",
                json={
                    "data": [
                        {
                            "id": "anthropic/claude-3-opus",
                            "context_length": 200000,
                            "supports_function_calling": True,
                            "supports_vision": True,
                            "supports_streaming": True,
                            "pricing": {"input": 0.015, "output": 0.075},
                        }
                    ]
                },
                status=200,
            )

            # Execute
            result = prober._probe_openrouter()

        # Verify
        assert "anthropic/claude-3-opus" in result
        assert result["anthropic/claude-3-opus"].context_length == 200000
        assert result["anthropic/claude-3-opus"].supports_function_calling is True
        assert result["anthropic/claude-3-opus"].supports_vision is True
        assert result["anthropic/claude-3-opus"].cost_per_1k_input_tokens == 0.015
        assert result["anthropic/claude-3-opus"].cost_per_1k_output_tokens == 0.075

    def test_probe_openrouter_without_api_key(self):
        """Test probing OpenRouter capabilities without an API key."""
        # Setup
        prober = CapabilityProber.get_instance()

        # Mock environment variable to remove API key
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": ""}):
            # Execute
            result = prober._probe_openrouter()

        # Verify
        assert "anthropic/claude-3-opus" in result  # Should use default capabilities
        assert "anthropic/claude-3-sonnet" in result
        assert "mistralai/mistral-large" in result

    @responses.activate
    def test_probe_openrouter_with_api_error(self):
        """Test probing OpenRouter capabilities when the API returns an error."""
        # Setup
        prober = CapabilityProber.get_instance()

        # Mock environment variable
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-api-key"}):
            # Mock API response with error
            responses.add(
                responses.GET,
                "https://openrouter.ai/api/v1/models",
                json={"error": "API error"},
                status=500,
            )

            # Execute
            result = prober._probe_openrouter()

        # Verify
        assert (
            "anthropic/claude-3-opus" in result
        )  # Should fall back to default capabilities
        assert "anthropic/claude-3-sonnet" in result
        assert "mistralai/mistral-large" in result

    def test_probe_openai(self):
        """Test probing OpenAI capabilities."""
        # Setup
        prober = CapabilityProber.get_instance()

        # Execute
        result = prober._probe_openai()

        # Verify
        assert "gpt-3.5-turbo" in result
        assert "gpt-4" in result
        assert "gpt-4-turbo" in result

        # Verify specific capabilities
        assert result["gpt-3.5-turbo"].context_length == 16385
        assert result["gpt-4"].supports_function_calling is True
        assert result["gpt-4-turbo"].supports_vision is True

    def test_probe_lmstudio(self):
        """Test probing LM Studio capabilities."""
        # Setup
        prober = CapabilityProber.get_instance()

        # Execute
        result = prober._probe_lmstudio()

        # Verify
        assert "lmstudio" in result
        assert result["lmstudio"].provider == "lmstudio"
        assert result["lmstudio"].context_length == 4096
        assert result["lmstudio"].supports_function_calling is False
        assert result["lmstudio"].supports_vision is False
        assert result["lmstudio"].supports_streaming is True
        assert result["lmstudio"].cost_per_1k_input_tokens == 0.0
        assert result["lmstudio"].cost_per_1k_output_tokens == 0.0

    def test_probe_dummy(self):
        """Test probing dummy provider capabilities."""
        # Setup
        prober = CapabilityProber.get_instance()

        # Execute
        result = prober._probe_dummy()

        # Verify
        assert "dummy" in result
        assert result["dummy"].provider == "dummy"
        assert result["dummy"].context_length == 1000
        assert result["dummy"].supports_function_calling is False
        assert result["dummy"].supports_vision is False
        assert result["dummy"].supports_streaming is False
        assert result["dummy"].cost_per_1k_input_tokens == 0.0
        assert result["dummy"].cost_per_1k_output_tokens == 0.0


class TestHelperFunctions:
    """Tests for the helper functions in the capabilities module."""

    def test_get_capability_prober(self):
        """Test the get_capability_prober function."""
        # Execute
        prober = get_capability_prober()

        # Verify
        assert isinstance(prober, CapabilityProber)
        assert prober is CapabilityProber.get_instance()

    @patch("autoresearch.llm.capabilities.get_capability_prober")
    def test_probe_all_providers_helper(self, mock_get_prober):
        """Test the probe_all_providers helper function."""
        # Setup
        mock_prober = MagicMock()
        mock_get_prober.return_value = mock_prober
        mock_prober.probe_all_providers.return_value = {"test": {}}

        # Execute
        result = probe_all_providers()

        # Verify
        assert result == {"test": {}}
        mock_prober.probe_all_providers.assert_called_once()

    @patch("autoresearch.llm.capabilities.get_capability_prober")
    def test_get_model_capabilities_helper(self, mock_get_prober):
        """Test the get_model_capabilities helper function."""
        # Setup
        mock_prober = MagicMock()
        mock_get_prober.return_value = mock_prober
        test_capabilities = ModelCapabilities(
            name="test-model",
            provider="test-provider",
            context_length=4096,
            supports_function_calling=True,
            supports_vision=False,
            supports_streaming=True,
            cost_per_1k_input_tokens=0.001,
            cost_per_1k_output_tokens=0.002,
        )
        mock_prober.get_model_capabilities.return_value = test_capabilities

        # Execute
        result = get_model_capabilities("test-model", "test-provider")

        # Verify
        assert result == test_capabilities
        mock_prober.get_model_capabilities.assert_called_once_with(
            "test-model", "test-provider"
        )
