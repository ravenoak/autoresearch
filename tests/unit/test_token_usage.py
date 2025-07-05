"""Tests for token usage tracking functionality.

This module contains tests for the token usage tracking functionality
in the orchestration system, ensuring that token counts are properly
recorded when using LLM adapters.
"""

from unittest.mock import MagicMock
from typing import Any

from autoresearch.orchestration.orchestrator import Orchestrator
from autoresearch.orchestration.metrics import OrchestrationMetrics
from autoresearch.llm import DummyAdapter, token_counting
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
    monkeypatch.setattr(llm, "get_pooled_adapter", lambda name: dummy_adapter)

    # Execute
    with Orchestrator._capture_token_usage("agent", metrics, mock_config) as (
        token_counter,
        wrapped_adapter,
    ):
        # Use the wrapped adapter returned by the context manager
        wrapped_adapter.generate("hello world")

    # Verify
    counts = metrics.token_counts["agent"]
    assert counts["in"] == 2  # "hello world" has 2 tokens
    assert counts["out"] > 0  # The output should have at least 1 token


def test_token_budget_truncates_prompt(monkeypatch):
    """Ensure prompts are truncated to the configured token budget."""

    metrics = OrchestrationMetrics()
    mock_config = MagicMock(spec=ConfigModel)
    mock_config.llm_backend = "dummy"
    mock_config.token_budget = 3

    dummy_adapter = DummyAdapter()
    monkeypatch.setattr(llm, "get_llm_adapter", lambda name: dummy_adapter)

    with Orchestrator._capture_token_usage("agent", metrics, mock_config) as (
        token_counter,
        wrapped_adapter,
    ):
        wrapped_adapter.generate("one two three four five")

    counts = metrics.token_counts["agent"]
    assert counts["in"] <= mock_config.token_budget


def test_prompt_passed_to_adapter_is_compressed(monkeypatch):
    """Prompts exceeding the budget are compressed before LLM generation."""

    metrics = OrchestrationMetrics()
    mock_config = MagicMock(spec=ConfigModel)
    mock_config.llm_backend = "dummy"
    mock_config.token_budget = 3

    dummy_adapter = DummyAdapter()
    captured: dict[str, str] = {}

    def spy_generate(prompt: str, model: str | None = None, **kwargs: Any) -> str:
        captured["prompt"] = prompt
        return "ok"

    dummy_adapter.generate = spy_generate
    monkeypatch.setattr(llm, "get_pooled_adapter", lambda name: dummy_adapter)

    with Orchestrator._capture_token_usage("agent", metrics, mock_config) as (
        _,
        wrapped_adapter,
    ):
        wrapped_adapter.generate("one two three four five")

    assert len(captured["prompt"].split()) <= mock_config.token_budget


def test_summarization_step_invoked():
    metrics = OrchestrationMetrics()
    dummy = DummyAdapter()
    captured: dict[str, Any] = {}

    def spy_generate(prompt: str, model: str | None = None, **kwargs: Any) -> str:
        captured["prompt"] = prompt
        return "ok"

    dummy.generate = spy_generate

    def summarizer(text: str, budget: int) -> str:
        captured["summarized"] = True
        return " ".join(text.split()[:budget])

    adapter = token_counting.TokenCountingAdapter(
        dummy, "agent", metrics, token_budget=3, summarize_excess=summarizer
    )
    adapter.generate("one two three four five")

    assert captured.get("summarized") is True
    assert len(captured["prompt"].split()) <= 3


def test_budget_accounts_for_agent_history():
    m = OrchestrationMetrics()
    budget = 5

    m.record_tokens("A", 8, 0)
    budget = m.suggest_token_budget(budget)
    assert budget >= 8

    m.record_tokens("B", 3, 0)
    budget_after = m.suggest_token_budget(budget)
    assert budget_after == 6
