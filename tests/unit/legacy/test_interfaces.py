# mypy: ignore-errors
"""Interface protocol tests.
Spec: docs/specs/interfaces.md
"""

from __future__ import annotations

from dataclasses import dataclass

from autoresearch.interfaces import QueryStateLike
from autoresearch.models import QueryResponse
from autoresearch.orchestration.state import QueryState


def test_query_state_complies() -> None:
    state = QueryState(query="test")
    assert isinstance(state, QueryStateLike)


def test_custom_state_complies() -> None:
    @dataclass
    class ToyState:
        cycle: int = 0

        def update(self, result: dict[str, object]) -> None:  # pragma: no cover
            self.data = result

        def synthesize(self) -> QueryResponse:  # pragma: no cover
            return QueryResponse(answer="", citations=[], reasoning=[], metrics={})

    assert isinstance(ToyState(), QueryStateLike)


def test_incomplete_state_rejected() -> None:
    class BrokenState:
        cycle = 0

        def update(self, result: dict[str, object]) -> None:  # pragma: no cover
            self.data = result

    assert not isinstance(BrokenState(), QueryStateLike)
