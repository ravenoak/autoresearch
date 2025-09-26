"""Task coordinator for executing planner task graphs."""

from __future__ import annotations

import time
from collections import deque
from enum import Enum
from typing import Any, Dict, Iterator, List, Mapping, Optional

from .phases import DialoguePhase
from .state import QueryState


class TaskStatus(str, Enum):
    """Lifecycle states for planned tasks."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETE = "complete"
    BLOCKED = "blocked"


class TaskCoordinator:
    """Coordinate execution of planned tasks and capture ReAct traces."""

    def __init__(self, state: QueryState, *, phase: DialoguePhase = DialoguePhase.RESEARCH) -> None:
        self.state = state
        self.phase = phase
        tasks_payload = state.task_graph.get("tasks", [])
        self._tasks: Dict[str, dict[str, Any]] = {
            task["id"]: dict(task) for task in tasks_payload if isinstance(task, Mapping)
        }
        self._status: Dict[str, TaskStatus] = {
            task_id: TaskStatus.PENDING for task_id in self._tasks
        }
        self._step_counter: Dict[str, int] = {task_id: 0 for task_id in self._tasks}
        self._dependency_cache: Dict[str, List[str]] = {
            task_id: list(task.get("depends_on", [])) for task_id, task in self._tasks.items()
        }
        self.state.metadata.setdefault("coordinator", {}).update(
            {
                "phase": self.phase.value,
                "task_count": len(self._tasks),
                "react_trace_count": len(self.state.react_traces),
            }
        )

    # ------------------------------------------------------------------
    # Task scheduling utilities
    # ------------------------------------------------------------------

    def ready_tasks(self) -> List[dict[str, Any]]:
        """Return tasks whose dependencies have been satisfied."""

        ready: List[dict[str, Any]] = []
        for task_id, task in self._tasks.items():
            if self._status.get(task_id) != TaskStatus.PENDING:
                continue
            deps = self._dependency_cache.get(task_id, [])
            if all(self._status.get(dep) == TaskStatus.COMPLETE for dep in deps if dep in self._status):
                ready.append(task)
        ready.sort(key=lambda item: item.get("metadata", {}).get("priority", 0))
        return ready

    def iter_schedule(self) -> Iterator[dict[str, Any]]:
        """Yield tasks in a dependency-respecting order."""

        visited: set[str] = set()
        queue: deque[str] = deque(task_id for task_id in self._tasks if not self._dependency_cache.get(task_id))
        queue.extend(task_id for task_id, deps in self._dependency_cache.items() if deps)

        while queue:
            task_id = queue.popleft()
            if task_id in visited or task_id not in self._tasks:
                continue
            deps = self._dependency_cache.get(task_id, [])
            if any(self._status.get(dep) != TaskStatus.COMPLETE for dep in deps if dep in self._tasks):
                queue.append(task_id)
                continue
            visited.add(task_id)
            yield self._tasks[task_id]

    def start_task(self, task_id: str) -> None:
        """Mark a task as running."""

        if task_id not in self._tasks:
            raise KeyError(f"Unknown task_id '{task_id}'")
        self._status[task_id] = TaskStatus.RUNNING

    def complete_task(self, task_id: str, *, output: Optional[Mapping[str, Any]] = None) -> None:
        """Mark a task as complete and persist optional outputs."""

        if task_id not in self._tasks:
            raise KeyError(f"Unknown task_id '{task_id}'")
        self._status[task_id] = TaskStatus.COMPLETE
        coordinator_meta = self.state.metadata.setdefault("coordinator", {})
        coordinator_meta.setdefault("completed", []).append(task_id)
        if output is not None:
            outputs = self.state.results.setdefault("task_outputs", {})
            outputs[task_id] = dict(output)

    def block_task(self, task_id: str, *, reason: str | None = None) -> None:
        """Mark a task as blocked with an optional reason."""

        if task_id not in self._tasks:
            raise KeyError(f"Unknown task_id '{task_id}'")
        self._status[task_id] = TaskStatus.BLOCKED
        if reason:
            coordinator_meta = self.state.metadata.setdefault("coordinator", {})
            coordinator_meta.setdefault("blocked", {})[task_id] = reason

    # ------------------------------------------------------------------
    # ReAct trace capture
    # ------------------------------------------------------------------

    def record_react_step(
        self,
        task_id: str,
        *,
        thought: str,
        action: str,
        observation: str | None = None,
        tool: str | None = None,
        metadata: Optional[Mapping[str, Any]] = None,
    ) -> dict[str, Any]:
        """Record a single ReAct step for the specified task."""

        if task_id not in self._tasks:
            raise KeyError(f"Unknown task_id '{task_id}'")
        self._step_counter[task_id] += 1
        trace_entry = {
            "task_id": task_id,
            "step": self._step_counter[task_id],
            "phase": self.phase.value,
            "thought": thought.strip(),
            "action": action.strip(),
            "observation": observation.strip() if isinstance(observation, str) else observation,
            "tool": tool,
            "metadata": dict(metadata) if metadata else {},
            "timestamp": time.time(),
        }
        self.state.add_react_trace(trace_entry)
        coordinator_meta = self.state.metadata.setdefault("coordinator", {})
        coordinator_meta["react_trace_count"] = len(self.state.react_traces)
        return trace_entry

    def replay_traces(self, task_id: Optional[str] = None) -> List[dict[str, Any]]:
        """Return captured traces for optional replay."""

        return self.state.get_react_traces(task_id=task_id)

    # ------------------------------------------------------------------
    # Status accessors
    # ------------------------------------------------------------------

    def status(self, task_id: str) -> TaskStatus:
        """Return the current status for a task."""

        if task_id not in self._tasks:
            raise KeyError(f"Unknown task_id '{task_id}'")
        return self._status[task_id]

    def summary(self) -> Mapping[str, Any]:
        """Return a summary of coordinator progress."""

        return {
            "phase": self.phase.value,
            "tasks": {task_id: status.value for task_id, status in self._status.items()},
            "react_traces": len(self.state.react_traces),
        }


__all__ = ["TaskCoordinator", "TaskStatus"]
