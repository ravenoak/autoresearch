"""Tests for parallel execution utilities."""

from __future__ import annotations

import time
from types import TracebackType
from typing import Any, Optional, Type

import pytest

from autoresearch.config.models import ConfigModel
from autoresearch.errors import OrchestrationError
from autoresearch.models import QueryResponse
from autoresearch.orchestration.parallel import execute_parallel_query
from autoresearch.orchestration.reasoning_payloads import FrozenReasoningStep


class DummyTracer:
    class _Span:
        def __enter__(self) -> "DummyTracer._Span":
            return self

        def __exit__(
            self,
            exc_type: Optional[Type[BaseException]],
            exc: Optional[BaseException],
            tb: Optional[TracebackType],
        ) -> None:  # pragma: no cover - no cleanup
            return None

        def set_attribute(self, *args: Any, **kwargs: Any) -> None:  # pragma: no cover - logging only
            return None

        def add_event(self, *args: Any, **kwargs: Any) -> None:  # pragma: no cover - logging only
            return None

    def start_as_current_span(self, name: str) -> "DummyTracer._Span":
        return DummyTracer._Span()


class DummySynthesizer:
    def execute(self, state: Any, config: ConfigModel) -> dict[str, str]:  # pragma: no cover - simple passthrough
        return {"answer": "combined"}


@pytest.fixture(autouse=True)
def patch_parallel(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "autoresearch.orchestration.parallel.setup_tracing", lambda *_: None
    )
    monkeypatch.setattr(
        "autoresearch.orchestration.parallel.get_tracer", lambda *_: DummyTracer()
    )
    monkeypatch.setattr(
        "autoresearch.orchestration.parallel._get_memory_usage", lambda: 0.0
    )
    monkeypatch.setattr(
        "autoresearch.orchestration.parallel._calculate_result_confidence",
        lambda _r: 0.5,
    )
    monkeypatch.setattr(
        "autoresearch.orchestration.parallel.AgentFactory.get",
        lambda _name: DummySynthesizer(),
    )


class SelectorOrchestrator:
    def run_query(self, query: str, config: ConfigModel) -> QueryResponse:
        agent = config.agents[0]
        if agent == "good":
            return QueryResponse(
                answer="good",
                citations=[],
                reasoning=["ok"],
                metrics={"token_usage": {"total": 1, "max_tokens": 10}},
            )
        if agent == "bad":  # pragma: no cover - error branch
            raise OrchestrationError("fail")
        if agent == "slow":  # pragma: no cover - timeout branch
            time.sleep(0.5)
            return QueryResponse(answer="slow", citations=[], reasoning=[], metrics={})
        raise OrchestrationError("unknown")


def test_execute_parallel_query_error_and_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "autoresearch.orchestration.orchestrator.Orchestrator",
        SelectorOrchestrator,
    )

    config = ConfigModel()
    resp_err = execute_parallel_query("q", config, [["good"], ["bad"]], timeout=1)
    meta_err = resp_err.metrics["parallel_execution"]
    assert meta_err["successful_groups"] == 1
    assert meta_err["error_groups"] == 1
    assert meta_err["timeout_groups"] == 0

    config2 = ConfigModel()
    resp_timeout = execute_parallel_query("q", config2, [["good"], ["slow"]], timeout=1)
    meta_timeout = resp_timeout.metrics["parallel_execution"]
    assert meta_timeout["successful_groups"] == 2  # Both complete within timeout
    assert meta_timeout["error_groups"] == 0
    assert meta_timeout["timeout_groups"] == 0


def test_execute_parallel_query_all_fail(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "autoresearch.orchestration.orchestrator.Orchestrator",
        SelectorOrchestrator,
    )

    config = ConfigModel()
    groups = [["bad"], ["bad"]]

    with pytest.raises(OrchestrationError):
        execute_parallel_query("q", config, groups, timeout=1)


def test_execute_parallel_query_reasoning_normalization(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "autoresearch.orchestration.orchestrator.Orchestrator",
        SelectorOrchestrator,
    )

    config = ConfigModel()
    groups = [["good"], ["good"]]

    first = execute_parallel_query("q", config, groups, timeout=1)
    second = execute_parallel_query("q", config, list(reversed(groups)), timeout=1)

    for payload in first.reasoning:
        assert isinstance(payload, FrozenReasoningStep)
        assert payload == payload["text"]
        assert hash(payload) == hash(payload["text"])

    assert [step["text"] for step in first.reasoning] == [
        step["text"] for step in second.reasoning
    ]
