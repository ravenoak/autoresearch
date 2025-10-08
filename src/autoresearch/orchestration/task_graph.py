"""Typed task graph structures shared across planner and coordinator."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, Sequence, TypedDict, Required


class TaskEdgePayload(TypedDict, total=False):
    """Typed payload for an edge between task nodes."""

    source: str
    target: str
    type: str


class TaskNodePayload(TypedDict, total=False):
    """Typed payload for a task node within the task graph."""

    id: str
    question: str
    tools: List[str]
    depends_on: List[str]
    criteria: List[str]
    affinity: Dict[str, float]
    metadata: Dict[str, Any]
    sub_questions: List[str]
    explanation: str
    dependency_depth: int
    dependency_rationale: str
    socratic_checks: List[str]


class TaskGraphPayload(TypedDict, total=False):
    """Typed payload for planner task graphs."""

    tasks: Required[List[TaskNodePayload]]
    edges: Required[List[TaskEdgePayload]]
    metadata: Required[Dict[str, Any]]
    objectives: List[str]
    exit_criteria: List[str]
    explanation: str


@dataclass(slots=True)
class TaskEdge:
    """Edge between task nodes."""

    source: str
    target: str
    type: str = "dependency"

    def to_payload(self) -> TaskEdgePayload:
        """Convert the edge into a serialisable payload."""

        return {"source": self.source, "target": self.target, "type": self.type}


@dataclass(slots=True)
class TaskNode:
    """Planner task node enriched with tool affinity metadata."""

    id: str
    question: str
    tools: List[str] = field(default_factory=list)
    depends_on: List[str] = field(default_factory=list)
    criteria: List[str] = field(default_factory=list)
    affinity: Dict[str, float] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    sub_questions: List[str] | None = None
    explanation: str | None = None
    dependency_depth: int | None = None
    dependency_rationale: str | None = None
    socratic_checks: List[str] = field(default_factory=list)

    def to_payload(self) -> TaskNodePayload:
        """Convert the node into a serialisable payload."""

        payload: TaskNodePayload = {
            "id": self.id,
            "question": self.question,
            "tools": list(self.tools),
            "depends_on": list(self.depends_on),
            "criteria": list(self.criteria),
            "affinity": dict(self.affinity),
            "metadata": dict(self.metadata),
        }
        if self.sub_questions:
            payload["sub_questions"] = list(self.sub_questions)
        if self.explanation:
            payload["explanation"] = self.explanation
        if self.dependency_depth is not None:
            payload["dependency_depth"] = int(self.dependency_depth)
        if self.dependency_rationale:
            payload["dependency_rationale"] = self.dependency_rationale
        if self.socratic_checks:
            payload["socratic_checks"] = list(self.socratic_checks)
        return payload


@dataclass(slots=True)
class TaskGraphNode:
    """Scheduler-friendly snapshot of a task node."""

    id: str
    question: str
    ready: bool
    dependency_depth: int
    pending_dependencies: List[str] = field(default_factory=list)
    affinity: Dict[str, float] = field(default_factory=dict)
    status: str = "pending"
    tools: List[str] = field(default_factory=list)
    criteria: List[str] = field(default_factory=list)
    explanation: str | None = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    socratic_checks: List[str] = field(default_factory=list)
    dependency_rationale: str | None = None

    def max_affinity(self) -> float:
        """Return the maximum affinity score across known tools."""

        if not self.affinity:
            return 0.0
        return max(self.affinity.values(), default=0.0)

    def ordering_key(self) -> tuple[int, float, int, int, str]:
        """Return a deterministic sort key for scheduling decisions."""

        ready_rank = 0 if self.ready else 1
        affinity_score = -self.max_affinity()
        pending_count = len(self.pending_dependencies)
        return ready_rank, affinity_score, self.dependency_depth, pending_count, self.id

    def is_available(self) -> bool:
        """Return ``True`` when the task can be scheduled immediately."""

        return self.ready and self.status == "pending"

    def to_snapshot(self) -> Dict[str, Any]:
        """Convert the node into a serialisable scheduler snapshot."""

        return {
            "id": self.id,
            "question": self.question,
            "ready": self.ready,
            "status": self.status,
            "dependency_depth": self.dependency_depth,
            "pending_dependencies": list(self.pending_dependencies),
            "tools": list(self.tools),
            "criteria": list(self.criteria),
            "explanation": self.explanation,
            "max_affinity": self.max_affinity(),
            "metadata": dict(self.metadata),
            "socratic_checks": list(self.socratic_checks),
            "dependency_rationale": self.dependency_rationale,
        }


@dataclass(slots=True)
class TaskGraph:
    """Typed container for planner task graphs."""

    tasks: List[TaskNode] = field(default_factory=list)
    edges: List[TaskEdge] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    objectives: List[str] = field(default_factory=list)
    exit_criteria: List[str] = field(default_factory=list)
    explanation: str | None = None

    def to_payload(self) -> TaskGraphPayload:
        """Convert the graph into a serialisable payload."""

        payload: TaskGraphPayload = {
            "tasks": [task.to_payload() for task in self.tasks],
            "edges": [edge.to_payload() for edge in self.edges],
            "metadata": dict(self.metadata),
        }
        if self.objectives:
            payload["objectives"] = list(self.objectives)
        if self.exit_criteria:
            payload["exit_criteria"] = list(self.exit_criteria)
        if self.explanation:
            payload["explanation"] = self.explanation
        return payload

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "TaskGraph":
        """Hydrate a ``TaskGraph`` from a mapping payload."""

        tasks_payload = payload.get("tasks", [])
        edges_payload = payload.get("edges", [])
        metadata_payload = payload.get("metadata", {})

        tasks: List[TaskNode] = []
        for index, node in enumerate(tasks_payload, start=1):
            if not isinstance(node, Mapping):
                continue
            task_id = str(node.get("id") or f"task-{index}")
            question = _extract_question(node)
            tools = _coerce_tools(node.get("tools"))
            depends_on = _coerce_strings(node.get("depends_on"))
            criteria = _coerce_strings(
                node.get("criteria") or node.get("exit_criteria")
            )
            sub_questions = _coerce_strings(
                node.get("sub_questions") or node.get("objectives")
            )
            affinity = _coerce_affinity(
                node.get("affinity") or node.get("tool_affinity")
            )
            raw_depth = node.get("dependency_depth")
            if raw_depth is None:
                raw_depth = node.get("depth")
            dependency_depth = _coerce_int(raw_depth)
            dependency_rationale = _coerce_text(
                node.get("dependency_rationale") or node.get("dependency_note")
            )
            socratic_checks = _coerce_socratic_checks(
                node.get("socratic_checks") or node.get("self_check")
            )
            metadata_field = node.get("metadata")
            task_metadata = (
                dict(metadata_field) if isinstance(metadata_field, Mapping) else {}
            )
            explanation_field = node.get("explanation")
            explanation = (
                explanation_field.strip()
                if isinstance(explanation_field, str) and explanation_field.strip()
                else None
            )
            tasks.append(
                TaskNode(
                    id=task_id,
                    question=question,
                    tools=tools,
                    depends_on=depends_on,
                    criteria=criteria,
                    affinity=affinity,
                    metadata=task_metadata,
                    sub_questions=sub_questions or None,
                    explanation=explanation,
                    dependency_depth=dependency_depth,
                    dependency_rationale=dependency_rationale,
                    socratic_checks=socratic_checks,
                )
            )

        edges: List[TaskEdge] = []
        for edge in edges_payload:
            if not isinstance(edge, Mapping):
                continue
            edges.append(
                TaskEdge(
                    source=str(edge.get("source")),
                    target=str(edge.get("target")),
                    type=str(edge.get("type", "dependency")),
                )
            )

        metadata: Dict[str, Any]
        if isinstance(metadata_payload, Mapping):
            metadata = dict(metadata_payload)
        else:
            metadata = {}

        dependency_overview = _coerce_dependency_overview(
            payload.get("dependency_overview")
            or metadata.get("dependency_overview")
        )
        if dependency_overview:
            metadata["dependency_overview"] = dependency_overview

        objectives = _coerce_strings(payload.get("objectives"))
        exit_criteria = _coerce_strings(payload.get("exit_criteria"))
        explanation_value = payload.get("explanation")
        explanation = (
            explanation_value.strip()
            if isinstance(explanation_value, str) and explanation_value.strip()
            else None
        )

        return cls(
            tasks=tasks,
            edges=edges,
            metadata=metadata,
            objectives=objectives,
            exit_criteria=exit_criteria,
            explanation=explanation,
        )

    @classmethod
    def from_planner_output(cls, payload: Any) -> "TaskGraph":
        """Hydrate a ``TaskGraph`` from planner output."""

        if isinstance(payload, TaskGraph):
            return payload
        if isinstance(payload, str):
            stripped = payload.strip()
            if not stripped:
                raise ValueError("planner output is empty")
            try:
                parsed = json.loads(stripped)
            except json.JSONDecodeError as exc:
                fence = re.search(
                    r"```(?:json)?\s*(.*?)```",
                    stripped,
                    flags=re.IGNORECASE | re.DOTALL,
                )
                if fence:
                    return cls.from_planner_output(fence.group(1))
                raise ValueError("planner output is not valid JSON") from exc
            return cls.from_planner_output(parsed)
        if isinstance(payload, Mapping):
            return cls.from_mapping(payload)
        if isinstance(payload, Sequence) and not isinstance(payload, (str, bytes)):
            return cls.from_mapping({"tasks": list(payload)})
        raise TypeError(
            "planner output must be a mapping, sequence, TaskGraph, or JSON string"
        )


def _coerce_strings(value: Any, *, split_pattern: str = r",|;|/|\n") -> List[str]:
    """Return a list of trimmed strings from ``value``."""

    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        return [
            segment.strip()
            for segment in re.split(split_pattern, value)
            if segment.strip()
        ]
    return []


def _coerce_tools(value: Any) -> List[str]:
    """Return tool identifiers from planner payloads."""

    if isinstance(value, Mapping):
        return [str(name).strip() for name in value.keys() if str(name).strip()]
    return _coerce_strings(value, split_pattern=r",|;|/|\n|\band\b")


def _coerce_int(value: Any) -> int | None:
    """Return a non-negative integer if ``value`` can be coerced."""

    if value is None:
        return None
    try:
        integer = int(value)
    except (TypeError, ValueError):
        return None
    if integer < 0:
        return None
    return integer


def _coerce_text(value: Any) -> str | None:
    """Return a trimmed string if ``value`` is text-like."""

    if isinstance(value, str):
        trimmed = value.strip()
        return trimmed or None
    if value is None:
        return None
    return str(value).strip() or None


def _coerce_socratic_checks(value: Any) -> List[str]:
    """Return Socratic self-check prompts from planner payloads."""

    if isinstance(value, Mapping):
        collected: List[str] = []
        for key, item in value.items():
            prefix = str(key).strip()
            nested_prompts = _coerce_socratic_checks(item)
            for prompt in nested_prompts:
                if prefix and not prompt.lower().startswith(prefix.lower()):
                    collected.append(f"{prefix}: {prompt}")
                else:
                    collected.append(prompt)
        return collected
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        flattened: List[str] = []
        for item in value:
            flattened.extend(_coerce_socratic_checks(item))
        return flattened
    if isinstance(value, str):
        parts = [segment.strip() for segment in re.split(r"\n|;|\|", value)]
        return [segment for segment in parts if segment]
    if value is None:
        return []
    text = str(value).strip()
    return [text] if text else []


def _coerce_dependency_overview(value: Any) -> List[Dict[str, Any]]:
    """Return a sanitised dependency overview payload."""

    if value is None:
        return []
    entries: List[Dict[str, Any]] = []
    items: Iterable[Any]
    if isinstance(value, Mapping):
        items = [value]
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        items = value
    else:
        return []
    for item in items:
        if not isinstance(item, Mapping):
            continue
        task_id = _coerce_text(item.get("task") or item.get("id"))
        depends_on = _coerce_strings(item.get("depends_on"))
        depth_value = item.get("depth")
        if depth_value is None:
            depth_value = item.get("dependency_depth")
        depth = _coerce_int(depth_value)
        rationale = _coerce_text(
            item.get("rationale")
            or item.get("dependency_rationale")
            or item.get("note")
        )
        entry: Dict[str, Any] = {}
        if task_id:
            entry["task"] = task_id
        if depends_on:
            entry["depends_on"] = depends_on
        if depth is not None:
            entry["depth"] = depth
        if rationale:
            entry["rationale"] = rationale
        if entry:
            entries.append(entry)
    return entries


def _parse_affinity_token(token: str) -> tuple[str, float] | None:
    """Parse a ``tool:score`` or ``tool score`` token into a tuple."""

    stripped = token.strip()
    for delimiter in (":", "=", " "):
        if delimiter in stripped:
            tool, score = stripped.split(delimiter, 1)
            tool_name = tool.strip()
            score_text = score.strip()
            if tool_name and _is_number(score_text):
                return tool_name, float(score_text)
    return None


def _coerce_affinity(value: Any) -> Dict[str, float]:
    """Return a numeric affinity mapping from planner payloads."""

    if isinstance(value, Mapping):
        return prune_affinity(value)

    cleaned: Dict[str, float] = {}
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for entry in value:
            if isinstance(entry, Mapping):
                cleaned.update(prune_affinity(entry))
            elif (
                isinstance(entry, Sequence)
                and not isinstance(entry, (str, bytes))
                and len(entry) == 2
            ):
                tool, score = entry
                if _is_number(score):
                    cleaned[str(tool).strip()] = float(score)
            elif isinstance(entry, str):
                parsed = _parse_affinity_token(entry)
                if parsed is not None:
                    tool, score = parsed
                    cleaned[tool] = score
        return cleaned

    if isinstance(value, str):
        for token in re.split(r",|;|/|\n", value):
            parsed = _parse_affinity_token(token)
            if parsed is not None:
                tool, score = parsed
                cleaned[tool] = score
    return cleaned


def _extract_question(node: Mapping[str, Any]) -> str:
    """Return the canonical question text for a task node."""

    for key in ("question", "goal", "description", "prompt", "task"):
        value = node.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _is_number(value: Any) -> bool:
    """Return ``True`` when ``value`` can be converted to ``float``."""

    try:
        float(value)
    except (TypeError, ValueError):
        return False
    return True


def prune_affinity(affinity: Mapping[str, Any]) -> Dict[str, float]:
    """Return a numeric affinity mapping, discarding invalid entries."""

    cleaned: Dict[str, float] = {}
    for tool, value in affinity.items():
        if _is_number(value):
            cleaned[str(tool)] = float(value)
    return cleaned


def merge_affinity(
    primary: Mapping[str, float],
    secondary: Iterable[tuple[str, float]],
) -> Dict[str, float]:
    """Merge affinity dictionaries while preserving the maximum score."""

    merged: Dict[str, float] = dict(primary)
    for tool, score in secondary:
        existing = merged.get(tool, float("-inf"))
        if score > existing:
            merged[tool] = score
    return merged


__all__ = [
    "TaskGraph",
    "TaskGraphPayload",
    "TaskNode",
    "TaskGraphNode",
    "TaskNodePayload",
    "TaskEdge",
    "TaskEdgePayload",
    "merge_affinity",
    "prune_affinity",
]
