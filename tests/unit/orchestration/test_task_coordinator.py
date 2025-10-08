"""Comprehensive tests for TaskCoordinator functionality."""

from __future__ import annotations

import pytest

from autoresearch.orchestration.coordinator import TaskCoordinator, TaskStatus
from autoresearch.orchestration.phases import DialoguePhase
from autoresearch.orchestration.state import QueryState


class TestTaskCoordinator:
    """Test suite for TaskCoordinator class."""

    @pytest.fixture
    def sample_state(self) -> QueryState:
        """Create a sample query state for testing."""
        return QueryState(
            query="test query",
            claims=[],
            claim_audits=[],
            sources=[],
            results={},
            messages=[],
            feedback_events=[],
            coalitions={},
            metadata={},
            task_graph={
                "tasks": [
                    {
                        "id": "task1",
                        "type": "research",
                        "content": "Research task 1",
                        "depends_on": [],
                        "metadata": {"priority": 1.0},
                    },
                    {
                        "id": "task2",
                        "type": "analysis",
                        "content": "Analysis task 2",
                        "depends_on": ["task1"],
                        "metadata": {"priority": 0.8},
                    },
                    {
                        "id": "task3",
                        "type": "synthesis",
                        "content": "Synthesis task 3",
                        "depends_on": ["task1", "task2"],
                        "metadata": {"priority": 0.9},
                    },
                ],
                "edges": [],
                "metadata": {},
            },
            react_log=[],
            react_traces=[],
            cycle=0,
            primus_index=0,
            last_updated=1234567890.0,
            error_count=0,
        )

    def test_coordinator_initialization(self, sample_state: QueryState) -> None:
        """Test TaskCoordinator initializes correctly."""
        coordinator = TaskCoordinator(sample_state, phase=DialoguePhase.RESEARCH)

        # Check basic initialization
        assert coordinator.state == sample_state
        assert coordinator.phase == DialoguePhase.RESEARCH
        assert len(coordinator._tasks) == 3
        assert all(task_id in coordinator._tasks for task_id in ["task1", "task2", "task3"])

        # Check status initialization
        assert all(status == TaskStatus.PENDING for status in coordinator._status.values())

        # Check dependency depths are computed (may be empty if no explicit depths provided)
        assert isinstance(coordinator._provided_depth, dict)
        assert isinstance(coordinator._dependency_depth, dict)

    def test_ready_tasks_identifies_initial_tasks(self, sample_state: QueryState) -> None:
        """Test ready_tasks correctly identifies tasks with no dependencies."""
        coordinator = TaskCoordinator(sample_state)

        ready = coordinator.ready_tasks()
        ready_ids = [task["id"] for task in ready]

        # task1 should be ready (no dependencies)
        assert "task1" in ready_ids
        # task2 and task3 should not be ready (have dependencies)
        assert "task2" not in ready_ids
        assert "task3" not in ready_ids

    def test_task_scheduling_priority_ordering(self, sample_state: QueryState) -> None:
        """Test task scheduling respects priority and dependency ordering."""
        coordinator = TaskCoordinator(sample_state)

        # Get ready tasks and verify priority ordering
        ready = coordinator.ready_tasks()
        assert len(ready) == 1
        assert ready[0]["id"] == "task1"

        # Complete task1 and check task2 becomes ready
        coordinator.complete_task("task1")
        ready = coordinator.ready_tasks()
        ready_ids = [task["id"] for task in ready]
        assert "task2" in ready_ids
        assert "task3" not in ready_ids  # Still blocked by task2

        # Complete task2 and check task3 becomes ready
        coordinator.complete_task("task2")
        ready = coordinator.ready_tasks()
        ready_ids = [task["id"] for task in ready]
        assert "task3" in ready_ids

    def test_task_lifecycle_management(self, sample_state: QueryState) -> None:
        """Test complete task lifecycle: start, complete, block."""
        coordinator = TaskCoordinator(sample_state)

        # Start a task
        coordinator.start_task("task1")
        assert coordinator.status("task1") == TaskStatus.RUNNING

        # Complete a task
        coordinator.complete_task("task1", output={"result": "success"})
        assert coordinator.status("task1") == TaskStatus.COMPLETE

        # Block a task
        coordinator.block_task("task2", reason="Waiting for data")
        assert coordinator.status("task2") == TaskStatus.BLOCKED

    def test_dependency_resolution_with_cycles(self) -> None:
        """Test dependency resolution handles complex dependency graphs."""
        # Create a state with potential cycle
        state = QueryState(
            query="test cyclic dependencies",
            claims=[],
            claim_audits=[],
            sources=[],
            results={},
            messages=[],
            feedback_events=[],
            coalitions={},
            metadata={},
            task_graph={
                "tasks": [
                    {
                        "id": "a",
                        "type": "task",
                        "content": "Task A",
                        "depends_on": ["b"],  # A depends on B
                        "metadata": {"priority": 1.0},
                    },
                    {
                        "id": "b",
                        "type": "task",
                        "content": "Task B",
                        "depends_on": ["a"],  # B depends on A (cycle!)
                        "metadata": {"priority": 0.9},
                    },
                ],
                "edges": [],
                "metadata": {},
            },
            react_log=[],
            react_traces=[],
            cycle=0,
            primus_index=0,
            last_updated=1234567890.0,
            error_count=0,
        )

        coordinator = TaskCoordinator(state)

        # Should handle cycle gracefully - no tasks should be ready initially
        ready = coordinator.ready_tasks()
        assert len(ready) == 0

    def test_react_trace_recording(self, sample_state: QueryState) -> None:
        """Test ReAct trace recording functionality."""
        coordinator = TaskCoordinator(sample_state)

        # Record a ReAct step
        coordinator.record_react_step(
            "task1",
            thought="I need to research this topic",
            action="search",
            observation="Found relevant information",
        )

        # Verify trace was recorded
        traces = coordinator.replay_traces("task1")
        assert len(traces) == 1
        assert traces[0]["thought"] == "I need to research this topic"
        assert traces[0]["action"] == "search"

    def test_scheduler_snapshot_functionality(self, sample_state: QueryState) -> None:
        """Test scheduler snapshot provides comprehensive state information."""
        coordinator = TaskCoordinator(sample_state)

        # Complete one task
        coordinator.complete_task("task1")

        # Get scheduler snapshot
        snapshot = coordinator._scheduler_snapshot("task2")

        # Verify snapshot contains expected information
        assert "selected" in snapshot
        assert "candidates" in snapshot
        assert len(snapshot["candidates"]) == 3  # All tasks
        # Check that candidates list is properly structured
        assert all(isinstance(candidate, dict) for candidate in snapshot["candidates"])
        # Verify the snapshot contains the expected task information
        selected_task = snapshot["selected"]
        assert isinstance(selected_task, dict)
        assert "task_id" in selected_task or "id" in selected_task

    def test_metadata_adaptation(self) -> None:
        """Test metadata adaptation handles various input types."""
        state = QueryState(
            query="test metadata adaptation",
            claims=[],
            claim_audits=[],
            sources=[],
            results={},
            messages=[],
            feedback_events=[],
            coalitions={},
            metadata={},
            task_graph={
                "tasks": [
                    {
                        "id": "meta_test",
                        "type": "test",
                        "content": "Test metadata",
                        "metadata": {
                            "string_val": "test",
                            "int_val": 42,
                            "float_val": 3.14,
                            "bool_val": True,
                            "list_val": ["a", "b", "c"],
                            "dict_val": {"nested": "value"},
                        },
                    }
                ],
                "edges": [],
                "metadata": {},
            },
            react_log=[],
            react_traces=[],
            cycle=0,
            primus_index=0,
            last_updated=1234567890.0,
            error_count=0,
        )

        coordinator = TaskCoordinator(state)
        adapted = coordinator._adapt_metadata(state.task_graph["tasks"][0]["metadata"])

        # Verify metadata was properly adapted
        assert adapted["string_val"] == "test"
        assert adapted["int_val"] == 42
        assert adapted["float_val"] == 3.14
        assert adapted["bool_val"] is True
        assert adapted["list_val"] == ["a", "b", "c"]
        assert adapted["dict_val"] == {"nested": "value"}

    def test_dependency_list_coercion(self) -> None:
        """Test dependency list coercion handles various input formats."""
        state = QueryState(
            query="test dependency coercion",
            claims=[],
            claim_audits=[],
            sources=[],
            results={},
            messages=[],
            feedback_events=[],
            coalitions={},
            metadata={},
            task_graph={
                "tasks": [
                    {
                        "id": "dep_test",
                        "type": "test",
                        "content": "Test dependencies",
                        "depends_on": ["task1", "task2"],  # List format
                    },
                    {
                        "id": "dep_test2",
                        "type": "test",
                        "content": "Test string dependencies",
                        "depends_on": "task3,task4",  # String format
                    },
                ],
                "edges": [],
                "metadata": {},
            },
            react_log=[],
            react_traces=[],
            cycle=0,
            primus_index=0,
            last_updated=1234567890.0,
            error_count=0,
        )

        coordinator = TaskCoordinator(state)

        # Test list coercion
        dep_list = coordinator._coerce_dependency_list(["task1", "task2"])
        assert dep_list == ["task1", "task2"]

        # Test string coercion
        dep_list = coordinator._coerce_dependency_list("task3,task4")
        assert dep_list == ["task3", "task4"]

        # Test None/empty coercion
        dep_list = coordinator._coerce_dependency_list(None)
        assert dep_list == []

    def test_task_status_summary(self, sample_state: QueryState) -> None:
        """Test task status summary provides comprehensive state information."""
        coordinator = TaskCoordinator(sample_state)

        # Initially all tasks should be pending
        summary = coordinator.summary()
        assert summary["phase"] == DialoguePhase.RESEARCH.value
        assert len(summary["tasks"]) == 3
        assert all(status == TaskStatus.PENDING.value for status in summary["tasks"].values())

        # Complete one task
        coordinator.complete_task("task1")
        summary = coordinator.summary()
        assert summary["tasks"]["task1"] == TaskStatus.COMPLETE.value
        assert summary["tasks"]["task2"] == TaskStatus.PENDING.value
        assert summary["tasks"]["task3"] == TaskStatus.PENDING.value

        # Start another task
        coordinator.start_task("task2")
        summary = coordinator.summary()
        assert summary["tasks"]["task1"] == TaskStatus.COMPLETE.value
        assert summary["tasks"]["task2"] == TaskStatus.RUNNING.value
        assert summary["tasks"]["task3"] == TaskStatus.PENDING.value

    def test_complex_dependency_resolution(self) -> None:
        """Test complex dependency scenarios with multiple levels."""
        state = QueryState(
            query="test complex dependencies",
            claims=[],
            claim_audits=[],
            sources=[],
            results={},
            messages=[],
            feedback_events=[],
            coalitions={},
            metadata={},
            task_graph={
                "tasks": [
                    {
                        "id": "root",
                        "type": "research",
                        "content": "Root task",
                        "depends_on": [],
                        "metadata": {"priority": 1.0},
                    },
                    {
                        "id": "level1_a",
                        "type": "analysis",
                        "content": "Level 1 task A",
                        "depends_on": ["root"],
                        "metadata": {"priority": 0.8},
                    },
                    {
                        "id": "level1_b",
                        "type": "analysis",
                        "content": "Level 1 task B",
                        "depends_on": ["root"],
                        "metadata": {"priority": 0.7},
                    },
                    {
                        "id": "level2",
                        "type": "synthesis",
                        "content": "Level 2 task",
                        "depends_on": ["level1_a", "level1_b"],
                        "metadata": {"priority": 0.9},
                    },
                ],
                "edges": [],
                "metadata": {},
            },
            react_log=[],
            react_traces=[],
            cycle=0,
            primus_index=0,
            last_updated=1234567890.0,
            error_count=0,
        )

        coordinator = TaskCoordinator(state)

        # Initially only root should be ready
        ready = coordinator.ready_tasks()
        ready_ids = [task["id"] for task in ready]
        assert ready_ids == ["root"]

        # Complete root task
        coordinator.complete_task("root")
        ready = coordinator.ready_tasks()
        ready_ids = [task["id"] for task in ready]
        # Both level1 tasks should now be ready
        assert "level1_a" in ready_ids
        assert "level1_b" in ready_ids
        assert "level2" not in ready_ids  # Still blocked

        # Complete both level1 tasks
        coordinator.complete_task("level1_a")
        coordinator.complete_task("level1_b")
        ready = coordinator.ready_tasks()
        ready_ids = [task["id"] for task in ready]
        # Level2 should now be ready
        assert "level2" in ready_ids
