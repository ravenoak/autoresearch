"""Tests for token usage tracking functionality.

This module contains tests for the token usage tracking functionality
in the orchestration system, ensuring that token counts are properly
recorded when using LLM adapters.
"""

import pytest
from unittest.mock import MagicMock

from autoresearch.orchestration.orchestrator import Orchestrator
from autoresearch.orchestration.metrics import OrchestrationMetrics
from autoresearch.llm import DummyAdapter
from autoresearch.config import ConfigModel
import autoresearch.llm as llm


def test_capture_token_usage_counts_correctly(monkeypatch):
    """Test that the token counting context manager correctly counts tokens.

    This test verifies that:
    1. The context manager returns both a token counter and a wrapped adapter
    2. The wrapped adapter correctly counts input and output tokens
    3. The token counts are recorded in the metrics
    """
    # Setup
    metrics = OrchestrationMetrics()

    # Create a mock config with llm_backend
    mock_config = MagicMock(spec=ConfigModel)
    mock_config.llm_backend = "dummy"

    # Set up the mock adapter
    dummy_adapter = DummyAdapter()
    monkeypatch.setattr(llm, "get_llm_adapter", lambda name: dummy_adapter)

    # Execute
    with Orchestrator._capture_token_usage("agent", metrics, mock_config) as (token_counter, wrapped_adapter):
        # Use the wrapped adapter returned by the context manager
        wrapped_adapter.generate("hello world")

    # Verify
    counts = metrics.token_counts["agent"]
    assert counts["in"] == 2  # "hello world" has 2 tokens
    assert counts["out"] > 0  # The output should have at least 1 token
