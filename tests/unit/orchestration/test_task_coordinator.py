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


def test_task_coordinator_schedules_dependencies(state_with_graph: QueryState) -> None:
    coordinator = TaskCoordinator(state_with_graph)

    schedule_order = [task["id"] for task in coordinator.iter_schedule()]
    assert schedule_order == ["t3", "t1", "t2"]

    ready = coordinator.ready_tasks()
    assert [task["id"] for task in ready] == ["t3", "t1"]

    coordinator.start_task("t3")
    coordinator.complete_task("t3")

    coordinator.start_task("t1")
    coordinator.complete_task("t1", output={"summary": "done"})

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
    assert (
        state_with_graph.metadata["coordinator"]["ordering_strategy"]
        == "depth_affinity"
    )
