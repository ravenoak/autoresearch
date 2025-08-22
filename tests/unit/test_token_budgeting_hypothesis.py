from __future__ import annotations

from unittest.mock import MagicMock
from typing import Any
import string

import pytest
from hypothesis import HealthCheck, given, settings, strategies as st

import autoresearch.llm as llm
from autoresearch.config.models import ConfigModel
from autoresearch.orchestration import token_utils
from autoresearch.orchestration.metrics import OrchestrationMetrics


@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    words=st.lists(
        st.text(alphabet=string.ascii_letters, min_size=1, max_size=5),
        min_size=1,
        max_size=20,
    ),
    budget=st.integers(min_value=1, max_value=20),
)
def test_capture_token_usage_respects_budget(
    words: list[str],
    budget: int,
    monkeypatch: pytest.MonkeyPatch,
    flexible_llm_adapter,
) -> None:
    """Prompts exceeding ``token_budget`` are compressed before counting.

    References: docs/algorithms/token_budgeting.md
    """
    metrics = OrchestrationMetrics()
    mock_config = MagicMock(spec=ConfigModel)
    mock_config.llm_backend = "flexible"
    mock_config.token_budget = budget

    captured: dict[str, str] = {}

    def spy_generate(prompt: str, model: str | None = None, **kwargs: Any) -> str:
        captured["prompt"] = prompt
        return "ok"

    flexible_llm_adapter.generate = spy_generate
    monkeypatch.setattr(llm, "get_pooled_adapter", lambda name: flexible_llm_adapter)

    prompt = " ".join(words)
    with token_utils._capture_token_usage("agent", metrics, mock_config) as (_, adapter):
        adapter.generate(prompt)

    counts = metrics.token_counts["agent"]
    tokens_in = counts["in"]
    original_len = len(prompt.split())
    limit = original_len if original_len <= budget else max(budget, 3)
    assert tokens_in <= limit
    if original_len <= budget:
        assert tokens_in == original_len
    assert len(captured["prompt"].split()) == tokens_in
