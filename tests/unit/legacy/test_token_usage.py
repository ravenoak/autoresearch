# mypy: ignore-errors
"""Tests for token usage tracking functionality.

This module contains tests for the token usage tracking functionality
in the orchestration system, ensuring that token counts are properly
recorded when using LLM adapters.
"""

from unittest.mock import MagicMock
from typing import Any

import pytest

from autoresearch.orchestration.orchestration_utils import OrchestrationUtils
from autoresearch.orchestration.metrics import OrchestrationMetrics
from autoresearch.config.models import ConfigModel
from autoresearch.llm.token_counting import compress_prompt
import autoresearch.llm as llm


def test_capture_token_usage_counts_correctly(
    monkeypatch: pytest.MonkeyPatch, flexible_llm_adapter: Any
) -> None:
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
    mock_config.llm_backend = "flexible"
    monkeypatch.setattr(llm, "get_pooled_adapter", lambda name: flexible_llm_adapter)

    # Execute
    with OrchestrationUtils.capture_token_usage("agent", metrics, mock_config) as (
        token_counter,
        wrapped_adapter,
    ):
        # Use the wrapped adapter returned by the context manager
        wrapped_adapter.generate("hello world")

    # Verify
    counts: dict[str, int] = metrics.token_counts["agent"]
    assert counts["in"] == 2  # "hello world" has 2 tokens
    assert counts["out"] > 0  # The output should have at least 1 token


def test_token_budget_truncates_prompt(
    monkeypatch: pytest.MonkeyPatch, flexible_llm_adapter: Any
) -> None:
    """Ensure prompts are truncated to the configured token budget."""

    metrics = OrchestrationMetrics()
    mock_config = MagicMock(spec=ConfigModel)
    mock_config.llm_backend = "flexible"
    mock_config.token_budget = 3

    monkeypatch.setattr(llm, "get_llm_adapter", lambda name: flexible_llm_adapter)

    with OrchestrationUtils.capture_token_usage("agent", metrics, mock_config) as (
        token_counter,
        wrapped_adapter,
    ):
        wrapped_adapter.generate("one two three four five")

    counts: dict[str, int] = metrics.token_counts["agent"]
    assert counts["in"] <= mock_config.token_budget


def test_prompt_passed_to_adapter_is_compressed(
    monkeypatch: pytest.MonkeyPatch, flexible_llm_adapter: Any
) -> None:
    """Prompts exceeding the budget are compressed before LLM generation."""

    metrics = OrchestrationMetrics()
    mock_config = MagicMock(spec=ConfigModel)
    mock_config.llm_backend = "flexible"
    mock_config.token_budget = 3

    captured: dict[str, str] = {}

    def spy_generate(prompt: str, model: str | None = None, **kwargs: Any) -> str:
        captured["prompt"] = prompt
        return "ok"

    flexible_llm_adapter.generate = spy_generate
    monkeypatch.setattr(llm, "get_pooled_adapter", lambda name: flexible_llm_adapter)

    with OrchestrationUtils.capture_token_usage("agent", metrics, mock_config) as (
        _,
        wrapped_adapter,
    ):
        wrapped_adapter.generate("one two three four five")

    assert len(captured["prompt"].split()) <= mock_config.token_budget


def test_compress_prompt_with_summarizer() -> None:
    """Summarizer is used when prompt exceeds the budget."""

    called = {}

    def summarizer(prompt: str, budget: int) -> str:
        called["p"] = prompt
        return "short summary"

    result = compress_prompt("one two three four five", 3, summarizer)
    assert result == "short summary"
    assert "p" in called


def test_summarizer_skipped_when_within_budget() -> None:
    """Summarizer is ignored when the prompt already fits the budget."""

    called = {}

    def summarizer(prompt: str, budget: int) -> str:  # pragma: no cover - should not run
        called["p"] = prompt
        return "unused"

    result = compress_prompt("one two", 3, summarizer)
    assert result == "one two"
    assert called == {}


def test_summarizer_fallback_to_truncation() -> None:
    """If the summary is too long an ellipsis-based truncation is used."""

    def long_summary(prompt: str, budget: int) -> str:
        return "this summary exceeds the budget"

    result = compress_prompt("one two three four five", 3, long_summary)
    assert result.split()[1] == "..."
    assert len(result.split()) == 3


def test_budget_considers_agent_history() -> None:
    """Token budget suggestion accounts for per-agent history."""

    m = OrchestrationMetrics()
    budget = 10

    m.record_tokens("A", 5, 0)
    budget = m.suggest_token_budget(budget)
    assert budget == 6

    m.record_tokens("B", 30, 0)
    budget = m.suggest_token_budget(budget)
    assert budget == 33

    # ``B`` is idle in the next cycle, so its historical average decays
    m.record_tokens("A", 5, 0)
    budget = m.suggest_token_budget(budget)
    assert budget == 17
