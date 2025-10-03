"""Tests for the task coordinator orchestration helper."""

import pytest

from autoresearch.orchestration.coordinator import TaskCoordinator, TaskStatus
from autoresearch.orchestration.state import QueryState


@pytest.fixture
def state_with_graph() -> QueryState:
    state = QueryState(query="Coordinate tasks")
    state.set_task_graph(
        {
            "tasks": [
                {
                    "id": "t1",
                    "question": "Gather background information",
                    "tools": ["search"],
                    "affinity": {"search": 0.6},
                },
                {
                    "id": "t2",
                    "question": "Synthesize evidence",
                    "depends_on": ["t1"],
                    "tools": ["analysis"],
                    "criteria": ["include citations"],
                    "affinity": {"analysis": 0.9, "search": 0.3},
                },
                {
                    "id": "t3",
                    "question": "Collect expert interviews",
                    "tools": ["search"],
                    "affinity": {"search": 0.95},
                },
            ]
        }
    )
    return state


@pytest.fixture
def state_with_tie_breakers() -> QueryState:
    state = QueryState(query="Tie breaker tasks")
    state.set_task_graph(
        {
            "tasks": [
                {
                    "id": "root",
                    "question": "Collect foundational evidence",
                    "affinity": {"search": 0.9},
                },
                {
                    "id": "leaf",
                    "question": "Synthesize detailed findings",
                    "depends_on": ["root"],
                    "affinity": {"analysis": 0.7, "search": 0.7},
                },
                {
                    "id": "orphan",
                    "question": "Capture ancillary context",
                    "affinity": {"analysis": 0.7},
                },
            ]
        }
    )
    return state


def test_task_coordinator_schedules_dependencies(state_with_graph: QueryState) -> None:
    coordinator = TaskCoordinator(state_with_graph)

    next_task = coordinator.schedule_next()
    assert next_task and next_task["id"] == "t3"
    next_with_tool = coordinator.schedule_next(preferred_tool="analysis")
    assert next_with_tool and next_with_tool["id"] == "t3"

    schedule_order = [task["id"] for task in coordinator.iter_schedule()]
    assert schedule_order == ["t3", "t1", "t2"]

    ready = coordinator.ready_tasks()
    assert [task["id"] for task in ready] == ["t3", "t1"]

    coordinator.start_task("t3")
    coordinator.complete_task("t3")

    coordinator.start_task("t1")
    coordinator.complete_task("t1", output={"summary": "done"})

    analysis_next = coordinator.schedule_next(preferred_tool="analysis")
    assert analysis_next and analysis_next["id"] == "t2"

    ready_after_first = coordinator.ready_tasks()
    assert [task["id"] for task in ready_after_first] == ["t2"]

    coordinator.start_task("t2")
    trace = coordinator.record_react_step(
        "t2",
        thought="review notes",
        action="call analysis",
        observation="insight",
        tool="analysis",
    )
    assert trace["step"] == 1
    assert trace["metadata"]["task_depth"] == 1
    assert trace["metadata"]["affinity_delta"] == 0.0
    assert trace["metadata"]["unlock_events"] == ["t2"]
    assert state_with_graph.react_traces[0]["task_id"] == "t2"

    coordinator.complete_task("t2")
    summary = coordinator.summary()
    assert summary["tasks"]["t2"] == TaskStatus.COMPLETE.value
    assert state_with_graph.metadata["coordinator"]["completed"] == [
        "t3",
        "t1",
        "t2",
    ]
    coordinator_meta = state_with_graph.metadata["coordinator"]
    assert coordinator_meta["ordering_strategy"] == "readiness_affinity"
    assert coordinator_meta["decisions"], "scheduler decisions should be captured"
    decision_snapshot = coordinator_meta["decisions"][-1]
    assert decision_snapshot["task_id"] == "t2"
    scheduler_meta = trace["metadata"]["scheduler"]
    assert scheduler_meta["selected"]["id"] == "t2"
    assert scheduler_meta["selected"]["status"] == TaskStatus.RUNNING.value
    assert scheduler_meta["candidates"][0]["ready"] is True


def test_schedule_next_applies_tie_breakers(
    state_with_tie_breakers: QueryState,
) -> None:
    coordinator = TaskCoordinator(state_with_tie_breakers)

    first = coordinator.schedule_next()
    assert first and first["id"] == "root"

    coordinator.start_task("root")
    coordinator.complete_task("root")

    second = coordinator.schedule_next(preferred_tool="analysis")
    assert second and second["id"] == "orphan"

    coordinator.start_task("orphan")
    coordinator.complete_task("orphan")

    third = coordinator.schedule_next(preferred_tool="analysis")
    assert third and third["id"] == "leaf"

    coordinator.start_task("leaf")
    coordinator.complete_task("leaf")

    assert coordinator.schedule_next() is None
