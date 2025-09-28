"""Regression tests for :mod:`autoresearch.orchestration.state`."""

from __future__ import annotations

import pytest

from autoresearch.orchestration.state import QueryState


def test_query_state_cloudpickle_serialization_preserves_fields() -> None:
    """`cloudpickle` round-trips retain planner metadata and claims."""

    cloudpickle = pytest.importorskip("cloudpickle")

    state = QueryState(query="serial")
    state.claims.append({"id": "c1", "text": "claim"})
    state.metadata["planner"] = {"strategy": "map"}
    state.set_task_graph(
        {
            "objectives": ["Persist graph"],
            "tasks": [
                {
                    "id": "t1",
                    "question": "Q",
                    "tool_affinity": {"search": 0.4},
                    "exit_criteria": ["complete"],
                    "explanation": "baseline",
                }
            ],
            "edges": [],
        }
    )

    payload = cloudpickle.dumps(state)
    restored = cloudpickle.loads(payload)

    assert restored.claims == state.claims
    assert restored.metadata["planner"] == state.metadata["planner"]
    assert restored.task_graph == state.task_graph
    assert restored.metadata["planner"]["telemetry"] == state.metadata["planner"]["telemetry"]
