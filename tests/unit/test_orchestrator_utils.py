import pytest
from hypothesis import given, strategies as st

from autoresearch.orchestration.orchestrator import (
    Orchestrator,
    AgentError,
    NotFoundError,
    TimeoutError,
    OrchestrationError,
)
from autoresearch.models import QueryResponse
from autoresearch.orchestration.state import QueryState


@given(st.lists(st.integers()), st.integers())
def test_rotate_list_property(items, idx):
    rotated = Orchestrator._rotate_list(items, idx)
    if not items:
        assert rotated == []
    else:
        start = idx % len(items)
        assert rotated == items[start:] + items[:start]


@pytest.mark.parametrize(
    "exc, expected",
    [
        (TimeoutError("t"), "transient"),
        (NotFoundError("n"), "recoverable"),
        (AgentError("retry please"), "transient"),
        (AgentError("configuration bad"), "recoverable"),
        (AgentError("fatal"), "critical"),
        (OrchestrationError("boom"), "critical"),
        (Exception("bad"), "critical"),
    ],
)
def test_categorize_error(exc, expected):
    assert Orchestrator._categorize_error(exc) == expected


@given(
    st.integers(min_value=0, max_value=5),
    st.integers(min_value=0, max_value=20),
    st.integers(min_value=0, max_value=5),
)
def test_calculate_result_confidence(num_citations, reasoning_len, error_count):
    resp = QueryResponse(
        answer="a",
        citations=["c"] * num_citations,
        reasoning=["r"] * reasoning_len,
        metrics={
            "token_usage": {"total": 50, "max_tokens": 100},
            "errors": ["e"] * error_count,
        },
    )
    score = Orchestrator._calculate_result_confidence(resp)
    assert 0.1 <= score <= 1.0


def test_apply_recovery_strategy():
    state = QueryState(query="q")
    info = Orchestrator._apply_recovery_strategy(
        "A", "transient", Exception("e"), state
    )
    assert info["recovery_strategy"] == "retry_with_backoff"
    assert "fallback" in state.results

    state = QueryState(query="q")
    info = Orchestrator._apply_recovery_strategy(
        "A", "recoverable", Exception("e"), state
    )
    assert info["recovery_strategy"] == "fallback_agent"
    assert "fallback" in state.results

    state = QueryState(query="q")
    info = Orchestrator._apply_recovery_strategy(
        "A", "critical", Exception("e"), state
    )
    assert info["recovery_strategy"] == "fail_gracefully"
    assert "error" in state.results
