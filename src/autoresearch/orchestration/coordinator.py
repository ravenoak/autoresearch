"""Task coordinator for executing planner task graphs."""

from __future__ import annotations

import heapq
import time
import re
from enum import Enum
from typing import Any, Dict, Iterator, List, Mapping, Optional, Sequence, Tuple

from .phases import DialoguePhase
from .state import QueryState
from .task_graph import TaskGraphNode


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
        self._provided_depth: Dict[str, int] = {}
        for task_id, task in self._tasks.items():
            metadata_payload = task.get("metadata")
            task["metadata"] = self._adapt_metadata(metadata_payload)
            depth_value = self._coerce_depth(task.get("dependency_depth"))
            if depth_value is not None:
                self._provided_depth[task_id] = depth_value
        self._status: Dict[str, TaskStatus] = {
            task_id: TaskStatus.PENDING for task_id in self._tasks
        }
        self._step_counter: Dict[str, int] = {task_id: 0 for task_id in self._tasks}
        self._dependency_cache: Dict[str, List[str]] = {
            task_id: [
                dep
                for dep in self._coerce_dependency_list(task.get("depends_on"))
                if dep in self._tasks
            ]
            for task_id, task in self._tasks.items()
        }
        self._dependents: Dict[str, List[str]] = {}
        for task_id, dependencies in self._dependency_cache.items():
            for dependency in dependencies:
                self._dependents.setdefault(dependency, []).append(task_id)
        self._dependency_depth: Dict[str, int] = self._compute_dependency_depths()
        for task_id, provided_depth in self._provided_depth.items():
            baseline = self._dependency_depth.get(task_id, 0)
            self._dependency_depth[task_id] = max(baseline, provided_depth)
        self._affinity_map: Dict[str, Dict[str, float]] = {}
        for task_id, task in self._tasks.items():
            affinity_payload = task.get("affinity") or task.get("tool_affinity")
            if isinstance(affinity_payload, Mapping):
                self._affinity_map[task_id] = {
                    str(tool): float(score)
                    for tool, score in affinity_payload.items()
                    if isinstance(score, (int, float))
                }
            else:
                self._affinity_map[task_id] = {}
        coordinator_meta = self.state.metadata.setdefault("coordinator", {})
        coordinator_meta.update(
            {
                "phase": self.phase.value,
                "task_count": len(self._tasks),
                "react_trace_count": len(self.state.react_traces),
                "ordering_strategy": "readiness_affinity",
            }
        )

    # ------------------------------------------------------------------
    # Task scheduling utilities
    # ------------------------------------------------------------------

    def ready_tasks(self) -> List[dict[str, Any]]:
        """Return tasks whose dependencies have been satisfied."""

        nodes = [
            self._build_graph_node(task_id)
            for task_id in self._tasks
            if self._status.get(task_id) == TaskStatus.PENDING
        ]
        nodes.sort(key=lambda node: node.ordering_key())
        return [self._tasks[node.id] for node in nodes if node.is_available()]

    def schedule_next(
        self, *, preferred_tool: str | None = None
    ) -> dict[str, Any] | None:
        """Return the next task to execute respecting affinity ordering."""

        candidates: list[tuple[tuple[Any, ...], TaskGraphNode]] = []
        for task_id in self._tasks:
            if self._status.get(task_id) != TaskStatus.PENDING:
                continue
            node = self._build_graph_node(task_id)
            ready_rank = 0 if node.ready else 1
            affinity_score: float
            coverage_rank = 0
            if preferred_tool:
                affinity_score = node.affinity.get(preferred_tool, 0.0)
                coverage_rank = 0 if preferred_tool in node.affinity else 1
                if coverage_rank == 1 and affinity_score == 0.0:
                    affinity_score = node.max_affinity()
            else:
                affinity_score = node.max_affinity()
            key = (
                ready_rank,
                coverage_rank,
                -affinity_score,
                node.dependency_depth,
                len(node.pending_dependencies),
                node.id,
            )
            candidates.append((key, node))

        if not candidates:
            return None

        candidates.sort(key=lambda item: item[0])
        for _, node in candidates:
            if node.ready:
                return self._tasks[node.id]
        return None

    def _compute_dependency_depths(self) -> Dict[str, int]:
        """Compute dependency depth for each task id."""

        depth: Dict[str, int] = {}

        def resolve(task_id: str, trail: tuple[str, ...] = ()) -> int:
            if task_id in depth:
                return depth[task_id]
            if task_id in trail:
                return 0
            deps = [dep for dep in self._dependency_cache.get(task_id, []) if dep in self._tasks]
            if not deps:
                depth[task_id] = 0
                return 0
            computed = 1 + max(resolve(dep, trail + (task_id,)) for dep in deps)
            depth[task_id] = computed
            return computed

        for task_id in self._tasks:
            resolve(task_id)
        return depth

    def _schedule_key(self, task_id: str) -> Tuple[int, float, str]:
        """Return ordering key based on depth and affinity."""

        node = self._build_graph_node(task_id)
        ready_rank, affinity_score, depth, pending_count, identifier = node.ordering_key()
        return ready_rank * 1000 + depth + pending_count, affinity_score, identifier

    def _max_affinity(self, task_id: str) -> float:
        """Return the maximum affinity score for a task."""

        affinity_map = self._affinity_map.get(task_id)
        if not affinity_map:
            return 0.0
        return max(affinity_map.values(), default=0.0)

    def _collect_unlock_events(self) -> List[str]:
        """Return tasks currently unlocked by satisfied dependencies."""

        candidates: list[TaskGraphNode] = []
        for candidate, deps in self._dependency_cache.items():
            status = self._status.get(candidate)
            if status not in {TaskStatus.PENDING, TaskStatus.RUNNING}:
                continue
            if all(self._status.get(dep) == TaskStatus.COMPLETE for dep in deps if dep in self._tasks):
                candidates.append(self._build_graph_node(candidate))
        candidates.sort(key=lambda node: node.ordering_key())
        return [node.id for node in candidates]

    def _affinity_delta(self, task_id: str, tool: str) -> float:
        """Return the delta between best affinity and selected tool."""

        affinity_map = self._affinity_map.get(task_id, {})
        if not affinity_map:
            return 0.0
        top_score = max(affinity_map.values(), default=0.0)
        selected_score = affinity_map.get(str(tool), 0.0)
        return float(top_score - selected_score)

    def iter_schedule(self) -> Iterator[dict[str, Any]]:
        """Yield tasks in a dependency-respecting order."""

        visited: set[str] = set()
        pending: Dict[str, set[str]] = {
            task_id: {dep for dep in deps if dep in self._tasks}
            for task_id, deps in self._dependency_cache.items()
        }
        for task_id in self._tasks:
            pending.setdefault(task_id, set())

        heap: List[Tuple[int, float, str]] = []
        for task_id, deps in pending.items():
            if not deps:
                heapq.heappush(heap, self._schedule_key(task_id))

        while heap:
            _, _, task_id = heapq.heappop(heap)
            if task_id in visited or task_id not in self._tasks:
                continue
            visited.add(task_id)
            yield self._tasks[task_id]
            for dependent in self._dependents.get(task_id, []):
                if dependent in visited or dependent not in pending:
                    continue
                deps = pending[dependent]
                deps.discard(task_id)
                if not deps:
                    heapq.heappush(heap, self._schedule_key(dependent))

        for task_id in self._tasks:
            if task_id not in visited:
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
        metadata_payload = dict(metadata) if metadata else {}
        unlock_events = self._collect_unlock_events()
        if unlock_events:
            merged_events: set[str] = set()
            existing_unlocks = metadata_payload.get("unlock_events")
            if isinstance(existing_unlocks, list):
                merged_events.update(str(item) for item in existing_unlocks)
            merged_events.update(unlock_events)
            ordered_unlocks = sorted(merged_events, key=self._schedule_key)
            metadata_payload["unlock_events"] = ordered_unlocks
        else:
            metadata_payload.setdefault("unlock_events", [])
        if tool is not None:
            metadata_payload["affinity_delta"] = self._affinity_delta(task_id, tool)
        metadata_payload.setdefault(
            "task_depth", self._dependency_depth.get(task_id, 0)
        )
        task_metadata = self._tasks.get(task_id, {}).get("metadata", {})
        if task_metadata:
            metadata_payload.setdefault("task_metadata", dict(task_metadata))
        metadata_payload["scheduler"] = self._scheduler_snapshot(task_id)

        trace_entry = {
            "task_id": task_id,
            "step": self._step_counter[task_id],
            "phase": self.phase.value,
            "thought": thought.strip(),
            "action": action.strip(),
            "observation": observation.strip() if isinstance(observation, str) else observation,
            "tool": tool,
            "metadata": metadata_payload,
            "timestamp": time.time(),
        }
        self.state.add_react_trace(trace_entry)
        coordinator_meta = self.state.metadata.setdefault("coordinator", {})
        coordinator_meta["react_trace_count"] = len(self.state.react_traces)
        decisions = coordinator_meta.setdefault("decisions", [])
        decisions.append(
            {
                "task_id": task_id,
                "step": self._step_counter[task_id],
                "timestamp": trace_entry["timestamp"],
                "scheduler": metadata_payload["scheduler"],
                "task_metadata": dict(task_metadata) if task_metadata else {},
            }
        )
        return trace_entry

    def _build_graph_node(self, task_id: str) -> TaskGraphNode:
        """Return a :class:`TaskGraphNode` snapshot for scheduling telemetry."""

        task = self._tasks[task_id]
        status = self._status.get(task_id, TaskStatus.PENDING).value
        dependencies = [dep for dep in self._dependency_cache.get(task_id, []) if dep in self._tasks]
        pending_deps = [
            dep
            for dep in dependencies
            if self._status.get(dep) != TaskStatus.COMPLETE
        ]
        ready = not pending_deps
        affinity = dict(self._affinity_map.get(task_id, {}))
        tools_payload = task.get("tools") or []
        if isinstance(tools_payload, list):
            tools = [str(tool).strip() for tool in tools_payload if str(tool).strip()]
        else:
            tools = [str(tools_payload)] if tools_payload else []
        criteria_payload = task.get("criteria") or task.get("exit_criteria") or []
        if isinstance(criteria_payload, list):
            criteria = [str(item).strip() for item in criteria_payload if str(item).strip()]
        else:
            criteria = [str(criteria_payload)] if criteria_payload else []
        explanation_value = task.get("explanation")
        explanation = (
            explanation_value.strip()
            if isinstance(explanation_value, str) and explanation_value.strip()
            else None
        )
        metadata_payload = task.get("metadata")
        metadata = (
            dict(metadata_payload) if isinstance(metadata_payload, Mapping) else {}
        )
        provided_depth = self._coerce_depth(task.get("dependency_depth"))
        dependency_depth = (
            provided_depth if provided_depth is not None else self._dependency_depth.get(task_id, 0)
        )
        socratic_checks = self._coerce_socratic_checks(
            task.get("socratic_checks") or task.get("self_check")
        )
        dependency_rationale = self._coerce_text(task.get("dependency_rationale"))
        return TaskGraphNode(
            id=task_id,
            question=str(task.get("question", "")),
            ready=ready,
            dependency_depth=dependency_depth,
            pending_dependencies=pending_deps,
            affinity=affinity,
            status=status,
            tools=tools,
            criteria=criteria,
            explanation=explanation,
            metadata=metadata,
            socratic_checks=socratic_checks,
            dependency_rationale=dependency_rationale,
        )

    def _scheduler_snapshot(self, focus_task: str) -> Dict[str, Any]:
        """Return scheduler telemetry for the current decision."""

        candidates = [self._build_graph_node(task_id) for task_id in self._tasks]
        candidates.sort(key=lambda node: node.ordering_key())
        focus = self._build_graph_node(focus_task)
        return {
            "selected": focus.to_snapshot(),
            "candidates": [node.to_snapshot() for node in candidates],
        }

    @staticmethod
    def _adapt_metadata(metadata: Any) -> dict[str, Any]:
        """Coerce planner-provided metadata into JSON-friendly mappings."""

        if not isinstance(metadata, Mapping):
            return {}

        def adapt_value(value: Any) -> Any:
            if isinstance(value, Mapping):
                return {
                    str(k): adapt_value(v) for k, v in value.items() if v is not None
                }
            if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
                return [adapt_value(item) for item in value]
            if isinstance(value, (str, int, float, bool)) or value is None:
                return value
            return str(value)

        return {str(key): adapt_value(val) for key, val in metadata.items()}

    @staticmethod
    def _coerce_dependency_list(value: Any) -> List[str]:
        """Return a stable list of dependency identifiers."""

        if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
            return [str(item).strip() for item in value if str(item).strip()]
        if isinstance(value, str):
            return [segment.strip() for segment in re.split(r",|;|/|\n", value) if segment.strip()]
        if value is None:
            return []
        return [str(value).strip()] if str(value).strip() else []

    @staticmethod
    def _coerce_depth(value: Any) -> int | None:
        """Return a non-negative integer depth when available."""

        if value is None:
            return None
        try:
            depth = int(value)
        except (TypeError, ValueError):
            return None
        return depth if depth >= 0 else None

    @staticmethod
    def _coerce_text(value: Any) -> str | None:
        """Return a trimmed string when ``value`` is textual."""

        if isinstance(value, str):
            trimmed = value.strip()
            return trimmed or None
        if value is None:
            return None
        return str(value).strip() or None

    @classmethod
    def _coerce_socratic_checks(cls, value: Any) -> List[str]:
        """Flatten Socratic self-check payloads into string prompts."""

        if isinstance(value, Mapping):
            collected: list[str] = []
            for key, item in value.items():
                prefix = str(key).strip()
                for prompt in cls._coerce_socratic_checks(item):
                    if prefix and not prompt.lower().startswith(prefix.lower()):
                        collected.append(f"{prefix}: {prompt}")
                    else:
                        collected.append(prompt)
            return collected
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
            flattened: list[str] = []
            for item in value:
                flattened.extend(cls._coerce_socratic_checks(item))
            return flattened
        if isinstance(value, str):
            parts = [segment.strip() for segment in re.split(r"\n|;|\|", value)]
            return [segment for segment in parts if segment]
        if value is None:
            return []
        text = str(value).strip()
        return [text] if text else []

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
