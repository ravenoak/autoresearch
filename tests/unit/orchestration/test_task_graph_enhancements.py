"""Unit tests for enhanced planner task graph normalization and scheduling."""

from __future__ import annotations

from __future__ import annotations

from typing import Any

import pytest

from autoresearch.orchestration.coordinator import TaskCoordinator
from autoresearch.orchestration.state import QueryState
from autoresearch.orchestration.task_graph import TaskGraph


def _build_payload() -> dict[str, Any]:
    return {
        "tasks": [
            {
                "id": "plan",
                "question": "Plan investigation",
                "depends_on": [],
                "affinity": {"planner": 0.9},
                "dependency_depth": 0,
                "socratic_checks": [
                    "What user assumption could fail?",
                    "How do we test feasibility?",
                ],
                "dependency_rationale": "Kick-off task has no predecessors.",
            },
            {
                "id": "research",
                "question": "Research evidence",
                "depends_on": ["plan"],
                "affinity": {"search": 0.8},
                "self_check": {
                    "risks": ["What if the sources disagree?"],
                    "tests": "Confirm alignment across summaries",
                },
                "dependency_depth": 1,
                "dependency_rationale": "Requires approved outline.",
            },
        ],
        "dependency_overview": [
            {
                "task": "research",
                "depends_on": ["plan"],
                "depth": 1,
                "rationale": "Research builds on the planning deliverable.",
            }
        ],
    }


def test_task_graph_from_planner_output_preserves_dependency_metadata() -> None:
    """Planner payloads expose dependency depth, rationale, and Socratic checks."""

    payload = _build_payload()
    graph = TaskGraph.from_planner_output(payload)

    assert len(graph.tasks) == 2
    plan, research = graph.tasks
    assert plan.dependency_depth == 0
    assert plan.dependency_rationale == "Kick-off task has no predecessors."
    assert plan.socratic_checks == [
        "What user assumption could fail?",
        "How do we test feasibility?",
    ]
    assert research.dependency_depth == 1
    assert research.socratic_checks[0].lower().startswith("risks:")
    assert graph.metadata["dependency_overview"] == [
        {
            "task": "research",
            "depends_on": ["plan"],
            "depth": 1,
            "rationale": "Research builds on the planning deliverable.",
        }
    ]


def test_query_state_normalises_socratic_checks_and_overview() -> None:
    """QueryState retains Socratic prompts and dependency overview telemetry."""

    state = QueryState(query="normalisation")
    payload = _build_payload()
    warnings = state.set_task_graph(payload)

    assert warnings == []
    task_graph = state.task_graph
    assert task_graph is not None
    research = next(task for task in task_graph["tasks"] if task["id"] == "research")
    assert research["dependency_depth"] == 1
    assert any(entry.startswith("risks:") for entry in research["socratic_checks"])
    planner_metadata = state.metadata.get("planner")
    assert isinstance(planner_metadata, dict)
    telemetry = planner_metadata.get("telemetry")
    assert isinstance(telemetry, dict)
    assert telemetry["dependency_overview"][0]["task"] == "research"
    assert telemetry["tasks"][0]["dependency_depth"] == 0


def test_task_coordinator_uses_depth_and_affinity() -> None:
    """Coordinator scheduling respects dependency depth and tool affinity."""

    payload = {
        "tasks": [
            {
                "id": "root",
                "question": "Initial analysis",
                "affinity": {"analysis": 0.2},
                "dependency_depth": 0,
                "socratic_checks": ["Is scope validated?"],
            },
            {
                "id": "priority",
                "question": "High impact review",
                "affinity": {"analysis": 0.1},
                "dependency_depth": 2,
            },
            {
                "id": "followup",
                "question": "Follow-up synthesis",
                "depends_on": ["root"],
                "affinity": {"analysis": 0.6},
                "dependency_depth": 1,
            },
        ]
    }
    state = QueryState(query="scheduling")
    state.set_task_graph(payload)

    coordinator = TaskCoordinator(state)
    next_task = coordinator.schedule_next(preferred_tool="analysis")
    assert next_task is not None
    assert next_task["id"] == "root"

    coordinator.start_task("root")
    coordinator.complete_task("root")
    next_task_after_root = coordinator.schedule_next(preferred_tool="analysis")
    assert next_task_after_root is not None
    assert next_task_after_root["id"] == "followup"
    snapshot = coordinator._build_graph_node("followup").to_snapshot()
    assert snapshot["dependency_depth"] == 1
    assert snapshot["socratic_checks"] == []


if __name__ == "__main__":
    pytest.main([__file__])
