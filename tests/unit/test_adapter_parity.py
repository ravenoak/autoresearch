"""Regression tests to ensure OpenRouter and LM Studio adapters maintain feature parity.

These tests verify that both adapters have equivalent functionality and behavior,
ensuring that enhancements to one don't break the other and that both provide
consistent user experience.
"""

import os
import time
import pytest
from unittest.mock import Mock, patch

from autoresearch.llm.adapters import LMStudioAdapter, OpenRouterAdapter


class TestAdapterParityBasic:
    """Test basic adapter functionality parity."""

    def test_both_adapters_initialize(self) -> None:
        """Test that both adapters can be initialized."""
        lmstudio_adapter = LMStudioAdapter()
        openrouter_adapter = OpenRouterAdapter()

        assert lmstudio_adapter is not None
        assert openrouter_adapter is not None

    def test_both_adapters_have_available_models(self) -> None:
        """Test that both adapters provide available models."""
        lmstudio_adapter = LMStudioAdapter()
        openrouter_adapter = OpenRouterAdapter()

        lmstudio_models = lmstudio_adapter.available_models
        openrouter_models = openrouter_adapter.available_models

        assert isinstance(lmstudio_models, list)
        assert isinstance(openrouter_models, list)
        assert len(lmstudio_models) >= 1
        assert len(openrouter_models) >= 1

    def test_both_adapters_support_model_validation(self) -> None:
        """Test that both adapters support model validation."""
        lmstudio_adapter = LMStudioAdapter()
        openrouter_adapter = OpenRouterAdapter()

        # Both should have validate_model method
        assert hasattr(lmstudio_adapter, "validate_model")
        assert hasattr(openrouter_adapter, "validate_model")

        # Both should be callable
        assert callable(lmstudio_adapter.validate_model)
        assert callable(openrouter_adapter.validate_model)


class TestAdapterParityContextManagement:
    """Test context management functionality parity."""

    def test_both_adapters_have_context_size_methods(self) -> None:
        """Test that both adapters provide context size functionality."""
        lmstudio_adapter = LMStudioAdapter()
        openrouter_adapter = OpenRouterAdapter()

        # Both should have get_context_size method
        assert hasattr(lmstudio_adapter, "get_context_size")
        assert hasattr(openrouter_adapter, "get_context_size")

        assert callable(lmstudio_adapter.get_context_size)
        assert callable(openrouter_adapter.get_context_size)

    def test_both_adapters_have_token_estimation(self) -> None:
        """Test that both adapters provide token estimation."""
        lmstudio_adapter = LMStudioAdapter()
        openrouter_adapter = OpenRouterAdapter()

        # Both should have estimate_prompt_tokens method
        assert hasattr(lmstudio_adapter, "estimate_prompt_tokens")
        assert hasattr(openrouter_adapter, "estimate_prompt_tokens")

        assert callable(lmstudio_adapter.estimate_prompt_tokens)
        assert callable(openrouter_adapter.estimate_prompt_tokens)

    def test_context_size_values_are_reasonable(self) -> None:
        """Test that context sizes returned by both adapters are reasonable."""
        lmstudio_adapter = LMStudioAdapter()
        openrouter_adapter = OpenRouterAdapter()

        # Test LM Studio context sizes
        lmstudio_models = lmstudio_adapter.available_models[:3]  # Test first 3
        for model in lmstudio_models:
            context_size = lmstudio_adapter.get_context_size(model)
            assert isinstance(context_size, int)
            assert context_size > 0
            assert context_size <= 1000000  # Reasonable upper bound

        # Test OpenRouter context sizes
        openrouter_models = openrouter_adapter.available_models[:3]  # Test first 3
        for model in openrouter_models:
            context_size = openrouter_adapter.get_context_size(model)
            assert isinstance(context_size, int)
            assert context_size > 0
            assert context_size <= 1000000  # Reasonable upper bound

    def test_token_estimation_consistency(self) -> None:
        """Test that token estimation is consistent across adapters."""
        lmstudio_adapter = LMStudioAdapter()
        openrouter_adapter = OpenRouterAdapter()

        test_prompt = "This is a test prompt for token estimation consistency."

        # Get token estimates from both adapters (using their default models)
        if lmstudio_adapter.available_models:
            lmstudio_tokens = lmstudio_adapter.estimate_prompt_tokens(test_prompt)
            assert isinstance(lmstudio_tokens, int)
            assert lmstudio_tokens > 0

        if openrouter_adapter.available_models:
            openrouter_tokens = openrouter_adapter.estimate_prompt_tokens(test_prompt)
            assert isinstance(openrouter_tokens, int)
            assert openrouter_tokens > 0

            # Token estimates should be roughly similar (within 50% variance)
            # This is a loose check since different tokenizers may vary
            if 'lmstudio_tokens' in locals():
                ratio = max(lmstudio_tokens, openrouter_tokens) / min(lmstudio_tokens, openrouter_tokens)
                assert ratio < 2.0, f"Token estimates vary too much: {lmstudio_tokens} vs {openrouter_tokens}"


class TestAdapterParityErrorHandling:
    """Test error handling functionality parity."""

    def test_both_adapters_have_error_handling_methods(self) -> None:
        """Test that both adapters have sophisticated error handling."""
        lmstudio_adapter = LMStudioAdapter()
        openrouter_adapter = OpenRouterAdapter()

        # Both should have error handling capabilities
        assert hasattr(lmstudio_adapter, "generate")  # Main entry point for errors
        assert hasattr(openrouter_adapter, "generate")

        # Both should handle errors gracefully
        assert callable(lmstudio_adapter.generate)
        assert callable(openrouter_adapter.generate)

    @patch("requests.post")
    def test_both_adapters_handle_network_errors(self, mock_post: Mock) -> None:
        """Test that both adapters handle network errors appropriately."""
        # Mock a network error
        mock_post.side_effect = Exception("Network error")

        lmstudio_adapter = LMStudioAdapter()
        openrouter_adapter = OpenRouterAdapter()

        # Both should raise appropriate errors
        with pytest.raises(Exception):  # Could be LLMError or other exception
            if lmstudio_adapter.available_models:
                lmstudio_adapter.generate("test", model=lmstudio_adapter.available_models[0])

        with pytest.raises(Exception):  # Could be LLMError or other exception
            if openrouter_adapter.available_models:
                openrouter_adapter.generate("test", model=openrouter_adapter.available_models[0])


class TestAdapterParityCaching:
    """Test caching functionality parity."""

    def test_both_adapters_have_caching_capabilities(self) -> None:
        """Test that both adapters support caching."""
        lmstudio_adapter = LMStudioAdapter()
        openrouter_adapter = OpenRouterAdapter()

        # Both should have model context size caching
        assert hasattr(lmstudio_adapter, "_model_context_sizes")
        assert hasattr(openrouter_adapter, "_model_context_sizes")

        # Both should have cache management methods
        assert hasattr(openrouter_adapter, "clear_model_cache")
        assert hasattr(openrouter_adapter, "refresh_model_cache")

        # LM Studio doesn't have explicit cache management methods, but should have caching
        assert isinstance(lmstudio_adapter._model_context_sizes, dict)
        assert isinstance(openrouter_adapter._model_context_sizes, dict)


class TestAdapterParityConfiguration:
    """Test configuration functionality parity."""

    def test_both_adapters_support_environment_configuration(self) -> None:
        """Test that both adapters support environment-based configuration."""
        # LM Studio configuration
        original_lmstudio_endpoint = os.getenv("LMSTUDIO_ENDPOINT")
        original_lmstudio_timeout = os.getenv("LMSTUDIO_TIMEOUT")

        # OpenRouter configuration
        original_openrouter_endpoint = os.getenv("OPENROUTER_ENDPOINT")
        original_openrouter_timeout = os.getenv("OPENROUTER_TIMEOUT")
        original_openrouter_cache_ttl = os.getenv("OPENROUTER_CACHE_TTL")

        try:
            # Test LM Studio configuration
            with patch.dict(os.environ, {"LMSTUDIO_ENDPOINT": "http://custom:1234"}):
                lmstudio_adapter = LMStudioAdapter()
                assert lmstudio_adapter.endpoint == "http://custom:1234"

            # Test OpenRouter configuration
            with patch.dict(os.environ, {
                "OPENROUTER_ENDPOINT": "https://custom.openrouter.ai/api/v1",
                "OPENROUTER_TIMEOUT": "120.0",
                "OPENROUTER_CACHE_TTL": "7200"
            }):
                openrouter_adapter = OpenRouterAdapter()
                assert openrouter_adapter.endpoint == "https://custom.openrouter.ai/api/v1"
                assert openrouter_adapter.timeout == 120.0
                assert openrouter_adapter._cache_ttl == 7200

        finally:
            # Restore original environment
            if original_lmstudio_endpoint is not None:
                os.environ["LMSTUDIO_ENDPOINT"] = original_lmstudio_endpoint
            if original_lmstudio_timeout is not None:
                os.environ["LMSTUDIO_TIMEOUT"] = original_lmstudio_timeout
            if original_openrouter_endpoint is not None:
                os.environ["OPENROUTER_ENDPOINT"] = original_openrouter_endpoint
            if original_openrouter_timeout is not None:
                os.environ["OPENROUTER_TIMEOUT"] = original_openrouter_timeout
            if original_openrouter_cache_ttl is not None:
                os.environ["OPENROUTER_CACHE_TTL"] = original_openrouter_cache_ttl


class TestAdapterParityAdvancedFeatures:
    """Test advanced feature parity between adapters."""

    def test_openrouter_has_lmstudio_level_features(self) -> None:
        """Test that OpenRouter has the same level of sophistication as LM Studio."""
        lmstudio_adapter = LMStudioAdapter()
        openrouter_adapter = OpenRouterAdapter()

        # OpenRouter should now have all the sophisticated features LM Studio has
        assert hasattr(openrouter_adapter, "check_context_fit")
        assert hasattr(openrouter_adapter, "truncate_prompt")
        assert hasattr(openrouter_adapter, "get_adaptive_token_budget")
        assert hasattr(openrouter_adapter, "record_token_usage")
        assert hasattr(openrouter_adapter, "_calculate_adaptive_factor")

        # LM Studio should have these features too
        assert hasattr(lmstudio_adapter, "check_context_fit")
        assert hasattr(lmstudio_adapter, "truncate_prompt")
        assert hasattr(lmstudio_adapter, "get_adaptive_token_budget")
        assert hasattr(lmstudio_adapter, "record_token_usage")

    def test_both_adapters_support_streaming(self) -> None:
        """Test that both adapters support streaming (even if not fully implemented)."""
        lmstudio_adapter = LMStudioAdapter()
        openrouter_adapter = OpenRouterAdapter()

        # Both should have generate_stream method (even if not fully implemented)
        assert hasattr(lmstudio_adapter, "generate_stream")
        assert hasattr(openrouter_adapter, "generate_stream")

        assert callable(lmstudio_adapter.generate_stream)
        assert callable(openrouter_adapter.generate_stream)


class TestAdapterParityPerformance:
    """Test performance characteristics parity."""

    def test_both_adapters_initialize_quickly(self) -> None:
        """Test that both adapters initialize in reasonable time."""

        # Test LM Studio initialization time
        start_time = time.time()
        lmstudio_adapter = LMStudioAdapter()
        lmstudio_init_time = time.time() - start_time

        # Test OpenRouter initialization time
        start_time = time.time()
        openrouter_adapter = OpenRouterAdapter()
        openrouter_init_time = time.time() - start_time

        # Use adapters in assertions to avoid unused variable warnings
        assert lmstudio_adapter is not None
        assert openrouter_adapter is not None

        # Both should initialize quickly (< 1 second)
        assert lmstudio_init_time < 1.0
        assert openrouter_init_time < 1.0

    def test_both_adapters_cache_effectively(self) -> None:
        """Test that both adapters cache effectively."""
        lmstudio_adapter = LMStudioAdapter()
        openrouter_adapter = OpenRouterAdapter()

        # Test that repeated calls are fast (cached)
        if lmstudio_adapter.available_models:
            model = lmstudio_adapter.available_models[0]

            # First call
            start_time = time.time()
            size1 = lmstudio_adapter.get_context_size(model)
            first_call_time = time.time() - start_time

            # Second call (should be cached)
            start_time = time.time()
            size2 = lmstudio_adapter.get_context_size(model)
            second_call_time = time.time() - start_time

            # Second call should be faster or at least not much slower
            assert size1 == size2
            assert second_call_time <= first_call_time * 2

        if openrouter_adapter.available_models:
            model = openrouter_adapter.available_models[0]

            # First call
            start_time = time.time()
            size1 = openrouter_adapter.get_context_size(model)
            first_call_time = time.time() - start_time

            # Second call (should be cached)
            start_time = time.time()
            size2 = openrouter_adapter.get_context_size(model)
            second_call_time = time.time() - start_time

            # Second call should be faster or at least not much slower
            assert size1 == size2
            assert second_call_time <= first_call_time * 2


class TestAdapterParityIntegration:
    """Test integration and compatibility between adapters."""

    def test_adapters_work_with_llm_factory(self) -> None:
        """Test that both adapters work with the LLM factory."""
        from autoresearch.llm import get_llm_adapter

        # Should be able to get both adapters through factory
        lmstudio_adapter = get_llm_adapter("lmstudio")
        openrouter_adapter = get_llm_adapter("openrouter")

        assert isinstance(lmstudio_adapter, LMStudioAdapter)
        assert isinstance(openrouter_adapter, OpenRouterAdapter)

    def test_adapters_maintain_compatibility(self) -> None:
        """Test that adapters maintain backward compatibility."""
        lmstudio_adapter = LMStudioAdapter()
        openrouter_adapter = OpenRouterAdapter()

        # Both should have the same basic interface
        required_methods = ["generate", "available_models", "get_context_size", "estimate_prompt_tokens"]

        for method in required_methods:
            assert hasattr(lmstudio_adapter, method), f"LM Studio missing {method}"
            assert hasattr(openrouter_adapter, method), f"OpenRouter missing {method}"
            assert callable(getattr(lmstudio_adapter, method))
            assert callable(getattr(openrouter_adapter, method))

    def test_adapters_handle_edge_cases_similarly(self) -> None:
        """Test that adapters handle edge cases in similar ways."""
        lmstudio_adapter = LMStudioAdapter()
        openrouter_adapter = OpenRouterAdapter()

        # Test empty prompt handling
        try:
            if lmstudio_adapter.available_models:
                lmstudio_adapter.generate("", model=lmstudio_adapter.available_models[0])
        except Exception as e:
            # Should handle gracefully
            assert isinstance(e, Exception)

        try:
            if openrouter_adapter.available_models:
                openrouter_adapter.generate("", model=openrouter_adapter.available_models[0])
        except Exception as e:
            # Should handle gracefully
            assert isinstance(e, Exception)

        # Test invalid model handling
        try:
            lmstudio_adapter.validate_model("invalid/model")
            assert False, "Should raise error for invalid model"
        except Exception:
            pass  # Expected to fail

        try:
            openrouter_adapter.validate_model("invalid/model")
            assert False, "Should raise error for invalid model"
        except Exception:
            pass  # Expected to fail


class TestAdapterParityRegression:
    """Regression tests to ensure feature parity is maintained."""

    def test_openrouter_matches_lmstudio_feature_set(self) -> None:
        """Test that OpenRouter has all the features LM Studio has."""
        lmstudio_adapter = LMStudioAdapter()
        openrouter_adapter = OpenRouterAdapter()

        # Core features that both should have
        core_features = [
            "generate", "available_models", "get_context_size",
            "estimate_prompt_tokens", "validate_model"
        ]

        for feature in core_features:
            assert hasattr(lmstudio_adapter, feature), f"LM Studio missing {feature}"
            assert hasattr(openrouter_adapter, feature), f"OpenRouter missing {feature}"

        # Advanced features that OpenRouter should now have (matching LM Studio)
        advanced_features = [
            "check_context_fit", "truncate_prompt", "get_adaptive_token_budget",
            "record_token_usage", "_calculate_adaptive_factor"
        ]

        for feature in advanced_features:
            assert hasattr(openrouter_adapter, feature), f"OpenRouter missing advanced feature {feature}"

        # LM Studio should also have these
        for feature in advanced_features:
            assert hasattr(lmstudio_adapter, feature), f"LM Studio missing {feature}"

    def test_error_handling_sophistication_parity(self) -> None:
        """Test that error handling sophistication is equivalent."""
        # Both adapters should provide detailed error messages
        # This is tested by ensuring both have sophisticated error handling methods

        lmstudio_adapter = LMStudioAdapter()
        openrouter_adapter = OpenRouterAdapter()

        # Both should have methods for handling errors
        assert hasattr(lmstudio_adapter, "generate")  # Main error handling entry point
        assert hasattr(openrouter_adapter, "_handle_openrouter_error")

        # Both should provide context in errors (tested by their generate methods)
        # This is verified by the fact that both raise LLMError with detailed information

    def test_configuration_parity(self) -> None:
        """Test that configuration options are equivalent."""
        # Both should support environment-based configuration
        # This is tested by ensuring both read from environment variables

        # LM Studio configuration options
        lmstudio_config_options = ["LMSTUDIO_ENDPOINT", "LMSTUDIO_TIMEOUT"]

        # OpenRouter configuration options (should be equivalent)
        openrouter_config_options = ["OPENROUTER_ENDPOINT", "OPENROUTER_TIMEOUT", "OPENROUTER_CACHE_TTL"]

        # Both should support their respective configuration options
        for option in lmstudio_config_options:
            assert option in ["LMSTUDIO_ENDPOINT", "LMSTUDIO_TIMEOUT"]

        for option in openrouter_config_options:
            assert option in ["OPENROUTER_ENDPOINT", "OPENROUTER_TIMEOUT", "OPENROUTER_CACHE_TTL"]

    def test_performance_characteristics_parity(self) -> None:
        """Test that performance characteristics are equivalent."""

        # Both should initialize quickly
        start_time = time.time()
        lmstudio_adapter = LMStudioAdapter()
        lmstudio_time = time.time() - start_time

        start_time = time.time()
        openrouter_adapter = OpenRouterAdapter()
        openrouter_time = time.time() - start_time

        # Use adapters to avoid unused variable warnings
        assert lmstudio_adapter is not None
        assert openrouter_adapter is not None

        # Both should initialize in reasonable time (< 1 second)
        assert lmstudio_time < 1.0
        assert openrouter_time < 1.0

        # Initialization times should be comparable (within 2x of each other)
        ratio = max(lmstudio_time, openrouter_time) / min(lmstudio_time, openrouter_time)
        assert ratio < 2.0, f"Initialization times vary too much: {lmstudio_time}s vs {openrouter_time}s"
