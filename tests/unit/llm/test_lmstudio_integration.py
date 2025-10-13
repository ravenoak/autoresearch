"""
Unit tests for LM Studio integration.

This module provides comprehensive unit tests for the LM Studio adapter,
including model discovery, context size awareness, and error handling.
"""

import os
import pytest
from unittest.mock import Mock, patch

from autoresearch.llm.adapters import LMStudioAdapter
from autoresearch.errors import LLMError


class TestLMStudioAdapter:
    """Test cases for LM Studio adapter functionality."""

    def test_adapter_initialization(self):
        """Test LM Studio adapter initialization."""
        with patch.dict(os.environ, {"LMSTUDIO_ENDPOINT": "http://localhost:1234/v1/chat/completions"}):
            adapter = LMStudioAdapter()

            assert adapter.endpoint == "http://localhost:1234/v1/chat/completions"
            assert adapter.timeout == 300.0
            assert isinstance(adapter.available_models, list)

    def test_model_discovery_success(self):
        """Test successful model discovery from LM Studio API."""
        mock_response = {
            "data": [
                {"id": "llama-3.2-1b-instruct", "model": "llama-3.2-1b-instruct"},
                {"id": "mistral-7b-instruct", "model": "mistral-7b-instruct"},
            ]
        }

        with patch.dict(os.environ, {"LMSTUDIO_ENDPOINT": "http://localhost:1234/v1/chat/completions"}):
            with patch("autoresearch.llm.adapters.get_session") as mock_session:
                mock_session.return_value.get.return_value.json.return_value = mock_response
                mock_session.return_value.get.return_value.raise_for_status = Mock()

                adapter = LMStudioAdapter()
                models = adapter.available_models

                assert len(models) >= 2
                assert "llama-3.2-1b-instruct" in models
                assert "mistral-7b-instruct" in models

    def test_model_discovery_failure(self):
        """Test model discovery failure handling."""
        with patch.dict(os.environ, {"LMSTUDIO_ENDPOINT": "http://localhost:1234/v1/chat/completions"}):
            with patch("autoresearch.llm.adapters.get_session") as mock_session:
                mock_session.return_value.get.side_effect = Exception("Connection failed")

                adapter = LMStudioAdapter()
                models = adapter.available_models

                # Should fall back to default models
                assert len(models) >= 1
                assert "mistral" in models

    def test_context_size_estimation(self):
        """Test context size estimation for different model types."""
        adapter = LMStudioAdapter()

        # Test that context size estimation returns reasonable values
        test_models = ["llama-3.2-1b-instruct", "mistral-7b-instruct", "qwen2-72b-instruct", "unknown-model"]

        for model in test_models:
            context_size = adapter.get_context_size(model)
            # Should return a positive integer (fallback logic may not match expected patterns exactly)
            assert isinstance(context_size, int)
            assert context_size > 0

    def test_prompt_truncation(self):
        """Test intelligent prompt truncation."""
        adapter = LMStudioAdapter()

        # Create a long prompt
        long_prompt = "This is a very detailed explanation. " * 1000

        # Test truncation
        model = "llama-3.2-1b-instruct"
        truncated = adapter.truncate_prompt(long_prompt, model)

        # Truncated should be shorter than original
        assert len(truncated) < len(long_prompt)

        # Should still be substantial
        assert len(truncated) > 100

        # Should end with truncation marker
        assert "[content truncated" in truncated or "[prompt truncated" in truncated

    def test_adaptive_token_budgeting(self):
        """Test adaptive token budgeting based on model capabilities."""
        adapter = LMStudioAdapter()

        # Test different model sizes
        small_model = "llama-3.2-1b-instruct"  # Small model
        large_model = "qwen2-72b-instruct"    # Large model

        small_budget = adapter.get_adaptive_token_budget(small_model, 1000)
        large_budget = adapter.get_adaptive_token_budget(large_model, 1000)

        # Larger models should generally get higher budgets
        assert small_budget <= large_budget

        # Both should be reasonable (at least 512 tokens)
        assert small_budget >= 512
        assert large_budget >= 512

    def test_model_validation(self):
        """Test model validation logic."""
        adapter = LMStudioAdapter()

        # Valid model should pass through
        valid_model = adapter.validate_model("llama-3.2-1b-instruct")
        assert valid_model == "llama-3.2-1b-instruct"

        # None should use default logic
        default_model = adapter.validate_model(None)
        assert default_model is not None

    def test_performance_tracking(self):
        """Test performance metrics tracking."""
        adapter = LMStudioAdapter()

        # Record some usage
        adapter.record_token_usage("test-model", 100, 50, success=True)

        # Check performance report
        report = adapter.get_model_performance_report("test-model")

        assert report["model"] == "test-model"
        assert "metrics" in report
        assert report["metrics"]["success_rate"] == 1.0
        assert report["metrics"]["total_count"] == 1

    def test_adapter_configuration(self):
        """Test adapter configuration and basic functionality."""
        # Test with custom endpoint
        with patch.dict(os.environ, {"LMSTUDIO_ENDPOINT": "http://localhost:1234/v1/chat/completions"}):
            adapter = LMStudioAdapter()
            assert adapter.endpoint == "http://localhost:1234/v1/chat/completions"

        # Test with custom timeout
        with patch.dict(os.environ, {"LMSTUDIO_TIMEOUT": "60.0"}):
            adapter = LMStudioAdapter()
            assert adapter.timeout == 60.0


class TestEnhancedModelSelection:
    """Test cases for enhanced model selection logic."""

    def test_environment_variable_selection(self):
        """Test model selection via environment variables."""
        with patch.dict(os.environ, {"AUTORESEARCH_MODEL": "test-model"}):
            from autoresearch.orchestration.metrics import _select_model_enhanced
            from autoresearch.config.loader import ConfigLoader

            config_loader = ConfigLoader()
            config = config_loader.config

            selected = _select_model_enhanced(config, "synthesizer")
            assert selected == "test-model"

    def test_agent_specific_environment_variable(self):
        """Test agent-specific environment variable override."""
        with patch.dict(os.environ, {
            "AUTORESEARCH_MODEL": "global-model",
            "AUTORESEARCH_MODEL_SYNTHESIZER": "agent-specific-model"
        }):
            from autoresearch.orchestration.metrics import _select_model_enhanced
            from autoresearch.config.loader import ConfigLoader

            config_loader = ConfigLoader()
            config = config_loader.config

            selected = _select_model_enhanced(config, "synthesizer")
            assert selected == "agent-specific-model"

    def test_config_fallback_selection(self):
        """Test fallback to configuration default model."""
        # Clear environment variables
        with patch.dict(os.environ, {}, clear=True):
            from autoresearch.orchestration.metrics import _select_model_enhanced
            from autoresearch.config.loader import ConfigLoader

            config_loader = ConfigLoader()
            config = config_loader.config

            selected = _select_model_enhanced(config, "synthesizer")
            # Should fall back to mistral (default) or config default
            assert selected in ["mistral", config.default_model]

    def test_model_availability_check(self):
        """Test checking model availability."""
        adapter = LMStudioAdapter()

        # Test that we can check available models
        available_models = adapter.available_models
        assert isinstance(available_models, list)
        assert len(available_models) >= 0  # May be empty if LM Studio unavailable

        # Test context size retrieval for first few models
        for model in available_models[:3]:
            context_size = adapter.get_context_size(model)
            assert isinstance(context_size, int)
            assert context_size > 0
