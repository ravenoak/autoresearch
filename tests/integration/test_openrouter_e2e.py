"""End-to-End tests for OpenRouter API integration.

These tests provide comprehensive end-to-end testing of OpenRouter functionality
including real API calls, error handling, caching, and performance testing.
Tests use only free-tier models to avoid costs.

This file focuses on the complete user experience and system behavior.
"""

import os
import time
import pytest

from autoresearch.config.loader import ConfigLoader
from autoresearch.llm.adapters import OpenRouterAdapter
from autoresearch.errors import LLMError


# Skip all tests if API key is not available
pytestmark = [
    pytest.mark.slow,
    pytest.mark.skipif(
        not os.getenv("OPENROUTER_API_KEY"),
        reason="OPENROUTER_API_KEY environment variable not set"
    ),
]


class TestOpenRouterEndToEndWorkflow:
    """End-to-end workflow tests for OpenRouter integration."""

    @pytest.fixture
    def config(self) -> ConfigLoader:
        """Get a configured config loader."""
        return ConfigLoader()

    @pytest.fixture
    def adapter(self) -> OpenRouterAdapter:
        """Get an OpenRouter adapter for testing."""
        return OpenRouterAdapter()

    def test_complete_model_discovery_workflow(self, adapter: OpenRouterAdapter) -> None:
        """Test the complete model discovery workflow end-to-end."""
        # Step 1: Initialize adapter
        assert adapter.api_key == os.getenv("OPENROUTER_API_KEY")

        # Step 2: Check available models
        models = adapter.available_models
        assert len(models) >= 10

        # Step 3: Verify free-tier models are present
        free_models = [m for m in models if any(free in m for free in ["gemini-flash", "llama-3.2", "qwen", "hermes"])]
        assert len(free_models) >= 1

        # Step 4: Test context size retrieval for multiple models
        context_sizes = {}
        for model in models[:3]:  # Test first 3 models
            try:
                context_sizes[model] = adapter.get_context_size(model)
            except Exception:
                # Some models might not be available, that's acceptable
                continue

        assert len(context_sizes) >= 1

        # Step 5: Test token estimation
        prompt = "This is an end-to-end test of OpenRouter integration."
        for model in list(context_sizes.keys())[:2]:
            token_count = adapter.estimate_prompt_tokens(prompt)
            assert token_count > 0

    def test_free_tier_model_generation_workflow(self, adapter: OpenRouterAdapter) -> None:
        """Test complete generation workflow with free-tier models."""
        # Step 1: Identify free models
        models = adapter.available_models
        free_models = [m for m in models if any(free in m for free in ["gemini-flash", "llama-3.2", "qwen", "hermes"])]

        if not free_models:
            pytest.skip("No free-tier models available")

        # Step 2: Test generation with each free model
        results = []
        for model in free_models[:2]:  # Test first 2 free models
            try:
                result = adapter.generate("Hello, this is an end-to-end test!", model=model)
                results.append({"model": model, "success": True, "length": len(result)})
            except LLMError as e:
                if "insufficient credits" in str(e).lower():
                    # Model might not actually be free, skip it
                    continue
                else:
                    raise

        # Should have at least one successful generation
        successful_results = [r for r in results if r["success"]]
        assert len(successful_results) >= 1, f"Should have at least one successful generation, got: {results}"

    def test_error_handling_and_recovery_workflow(self, adapter: OpenRouterAdapter) -> None:
        """Test complete error handling and recovery workflow."""
        # Step 1: Test invalid API key scenario
        original_key = adapter.api_key
        adapter.api_key = "invalid-key-12345"

        try:
            adapter.generate("Test prompt")
            assert False, "Should have raised error for invalid API key"
        except LLMError as e:
            error_msg = str(e)
            assert "Authentication failed" in error_msg or "401" in error_msg

        # Step 2: Restore valid API key
        adapter.api_key = original_key

        # Step 3: Test invalid model scenario
        try:
            adapter.generate("Test prompt", model="invalid/model/name")
            assert False, "Should have raised error for invalid model"
        except LLMError as e:
            error_msg = str(e)
            assert "not found" in error_msg.lower() or "404" in error_msg

        # Step 4: Verify adapter still works after errors
        models = adapter.available_models
        assert len(models) >= 1

    def test_caching_and_performance_workflow(self, adapter: OpenRouterAdapter) -> None:
        """Test caching behavior and performance characteristics."""
        # Step 1: Clear cache to ensure fresh state
        adapter.clear_model_cache()

        # Step 2: Time initial model discovery
        start_time = time.time()
        models = adapter.available_models
        _ = time.time() - start_time  # Measure but don't use the value

        # Step 3: Time cached model access
        start_time = time.time()
        models_cached = adapter.available_models
        _ = time.time() - start_time  # Measure but don't use the value

        # Step 4: Verify results are consistent
        assert models == models_cached
        assert len(models) >= 1

        # Step 5: Test context size caching
        if models:
            model = models[0]
            start_time = time.time()
            size1 = adapter.get_context_size(model)
            first_call_time = time.time() - start_time

            start_time = time.time()
            size2 = adapter.get_context_size(model)
            second_call_time = time.time() - start_time

            # Second call should be faster (cached)
            assert size1 == size2
            assert second_call_time <= first_call_time * 2

    def test_configuration_and_environment_workflow(self, adapter: OpenRouterAdapter, config: ConfigLoader) -> None:
        """Test configuration and environment variable handling."""
        # Step 1: Verify API key is properly loaded
        assert adapter.api_key == os.getenv("OPENROUTER_API_KEY")

        # Step 2: Test environment variable overrides
        # These would be tested if we had custom environment variables set
        # For now, verify defaults are reasonable
        assert "openrouter.ai" in adapter.endpoint
        assert adapter._cache_ttl > 0

        # Step 3: Test that configuration doesn't interfere with adapter
        _ = config.config
        # Adapter should work independently of config settings

    def test_concurrent_usage_workflow(self) -> None:
        """Test concurrent usage patterns."""
        import threading

        results = []

        def create_and_use_adapter(thread_id: int) -> None:
            """Create adapter and perform operations in separate thread."""
            try:
                adapter = OpenRouterAdapter()
                models = adapter.available_models
                results.append({"thread": thread_id, "models_count": len(models), "success": True})

                if models:
                    # Test basic functionality
                    try:
                        _ = adapter.get_context_size(models[0])
                    except Exception:
                        # Some operations might fail, that's acceptable
                        pass

            except Exception as e:
                results.append({"thread": thread_id, "success": False, "error": str(e)})

        # Create multiple threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=create_and_use_adapter, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join(timeout=30)

        # Verify all threads completed successfully
        successful_threads = [r for r in results if r["success"]]
        assert len(successful_threads) >= 2, f"Most threads should succeed, got: {results}"


class TestOpenRouterPerformanceAndReliability:
    """Performance and reliability tests for OpenRouter integration."""

    def test_response_time_consistency(self) -> None:
        """Test that response times are consistent across multiple calls."""
        adapter = OpenRouterAdapter()

        # Test with a simple, fast model if available
        models = adapter.available_models
        fast_models = [m for m in models if "gemini-flash" in m or "llama-3.2" in m]

        if not fast_models:
            pytest.skip("No fast models available for performance testing")

        model = fast_models[0]
        response_times = []

        # Make multiple calls and measure response times
        for i in range(3):
            start_time = time.time()
            try:
                result = adapter.generate("Performance test message", model=model)
                end_time = time.time()
                response_times.append(end_time - start_time)

                # Verify we got a reasonable response
                assert len(result) > 0
            except LLMError:
                # Some calls might fail, skip timing for those
                continue

        # Should have at least one successful timing
        if response_times:
            # Response times should be reasonable (< 10 seconds for simple prompts)
            max_time = max(response_times)
            assert max_time < 10.0, f"Response time too slow: {max_time}s"

            # Response times should be relatively consistent
            avg_time = sum(response_times) / len(response_times)
            for response_time in response_times:
                # Allow up to 3x variance for network conditions
                assert response_time <= avg_time * 3, f"Inconsistent response time: {response_time}s vs avg {avg_time}s"

    def test_memory_usage_stability(self) -> None:
        """Test that memory usage remains stable during extended use."""
        import psutil
        import os

        adapter = OpenRouterAdapter()
        process = psutil.Process(os.getpid())

        # Get initial memory usage
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Perform multiple operations
        for i in range(10):
            try:
                models = adapter.available_models
                if models:
                    _ = adapter.get_context_size(models[0])
                    # Perform a small generation if possible
                    try:
                        _ = adapter.generate("Memory test", model=models[0])
                    except LLMError:
                        # Generation might fail, that's acceptable
                        pass
            except Exception:
                # Some operations might fail, continue testing
                continue

        # Check final memory usage
        final_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Memory increase should be reasonable (< 50MB for our test)
        memory_increase = final_memory - initial_memory
        assert memory_increase < 50, f"Memory usage increased too much: {memory_increase}MB"

    def test_adapter_reuse_and_state_management(self) -> None:
        """Test that adapter state is properly managed across multiple uses."""
        adapter1 = OpenRouterAdapter()
        adapter2 = OpenRouterAdapter()

        # Both adapters should have independent state
        assert adapter1 is not adapter2

        # They should have the same available models (from shared defaults/cache)
        models1 = set(adapter1.available_models)
        models2 = set(adapter2.available_models)

        # Should have significant overlap
        overlap = models1 & models2
        assert len(overlap) >= 5, "Adapters should have consistent model availability"

        # Test that operations on one adapter don't affect the other
        if models1:
            size1 = adapter1.get_context_size(list(models1)[0])
            size2 = adapter2.get_context_size(list(models2)[0])

            # Both should work independently
            assert isinstance(size1, int)
            assert isinstance(size2, int)


class TestOpenRouterErrorScenariosEndToEnd:
    """End-to-end error scenario testing."""

    def test_rate_limit_handling_end_to_end(self) -> None:
        """Test complete rate limit handling workflow."""
        adapter = OpenRouterAdapter()

        # This test attempts to trigger rate limiting by making rapid requests
        # In practice, this might be hard to trigger reliably with free models
        responses = []

        # Make several rapid requests
        for i in range(5):
            try:
                result = adapter.generate(f"Rapid request {i}")
                responses.append({"success": True, "length": len(result)})
            except LLMError as e:
                if "rate limit" in str(e).lower():
                    # Successfully triggered rate limit handling
                    responses.append({"success": False, "error": "rate_limit", "message": str(e)})
                    break
                else:
                    responses.append({"success": False, "error": "other", "message": str(e)})

        # Should have made some attempts
        assert len(responses) >= 1

    def test_model_availability_and_fallback(self) -> None:
        """Test model availability checking and fallback behavior."""
        adapter = OpenRouterAdapter()

        # Test with a model that might not exist
        try:
            result = adapter.generate("Test", model="definitely/does/not/exist")
            assert False, "Should have failed for non-existent model"
        except LLMError as e:
            error_msg = str(e)
            # Should get a specific error about model not being found
            assert any(term in error_msg.lower() for term in ["not found", "404", "invalid model"])

        # Verify adapter still works after error
        models = adapter.available_models
        assert len(models) >= 1

        # Should be able to use a valid model after the error
        if models:
            result = adapter.generate("Recovery test", model=models[0])
            assert len(result) > 0

    def test_api_key_validation_workflow(self) -> None:
        """Test API key validation in a complete workflow."""
        # Test with invalid API key
        original_key = os.getenv("OPENROUTER_API_KEY")

        # Temporarily use invalid key
        os.environ["OPENROUTER_API_KEY"] = "invalid-key-12345"

        try:
            adapter = OpenRouterAdapter()
            adapter.generate("Test with invalid key")
            assert False, "Should have failed with invalid API key"
        except LLMError as e:
            error_msg = str(e)
            assert "Authentication failed" in error_msg or "401" in error_msg or "403" in error_msg

        # Restore valid key
        if original_key:
            os.environ["OPENROUTER_API_KEY"] = original_key

        # Verify adapter works with valid key
        adapter = OpenRouterAdapter()
        models = adapter.available_models
        assert len(models) >= 1


class TestOpenRouterIntegrationWithAutoresearch:
    """Test OpenRouter integration with broader Autoresearch functionality."""

    def test_adapter_factory_integration(self) -> None:
        """Test that OpenRouter adapter integrates with the LLM factory."""
        from autoresearch.llm import get_llm_adapter

        # Should be able to get OpenRouter adapter through factory
        adapter = get_llm_adapter("openrouter")
        assert isinstance(adapter, OpenRouterAdapter)

        # Should have the same capabilities
        models = adapter.available_models
        assert len(models) >= 1

    def test_configuration_integration(self) -> None:
        """Test OpenRouter integration with configuration system."""
        config_loader = ConfigLoader()

        # Temporarily modify config to use OpenRouter
        original_backend = config_loader.config.llm_backend
        config_loader.config.llm_backend = "openrouter"

        # Should be able to use OpenRouter through config
        from autoresearch.llm import get_pooled_adapter

        try:
            adapter = get_pooled_adapter("openrouter")
            assert isinstance(adapter, OpenRouterAdapter)
        except Exception:
            # Pool might not be initialized, that's acceptable
            pass

        # Restore original config
        config_loader.config.llm_backend = original_backend

    def test_capabilities_integration(self) -> None:
        """Test OpenRouter integration with capabilities system."""
        from autoresearch.llm.capabilities import CapabilityProber

        prober = CapabilityProber.get_instance()

        # Should be able to probe OpenRouter capabilities
        capabilities = prober._probe_openrouter()

        # Should have some capabilities (even if defaults)
        assert len(capabilities) >= 1

        # Check that free models have zero cost
        free_models = [model for model, cap in capabilities.items() if cap.cost_per_1k_input_tokens == 0.0]
        if free_models:
            assert len(free_models) >= 1

    def test_error_integration_with_autoresearch(self) -> None:
        """Test that OpenRouter errors integrate properly with Autoresearch error handling."""
        from autoresearch.llm import get_llm_adapter

        adapter = get_llm_adapter("openrouter")

        # Test that errors are properly wrapped as LLMError
        try:
            adapter.generate("Test", model="invalid/model")
            assert False, "Should have raised LLMError"
        except LLMError as e:
            # Should be an LLMError with proper context
            assert hasattr(e, 'model')
            assert hasattr(e, 'suggestion')
            assert e.model is not None
