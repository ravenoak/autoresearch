"""Typed task graph structures shared across planner and coordinator."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, TypedDict


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


class TaskGraphPayload(TypedDict):
    """Typed payload for planner task graphs."""

    tasks: List[TaskNodePayload]
    edges: List[TaskEdgePayload]
    metadata: Dict[str, Any]


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
        }


@dataclass(slots=True)
class TaskGraph:
    """Typed container for planner task graphs."""

    tasks: List[TaskNode] = field(default_factory=list)
    edges: List[TaskEdge] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_payload(self) -> TaskGraphPayload:
        """Convert the graph into a serialisable payload."""

        return {
            "tasks": [task.to_payload() for task in self.tasks],
            "edges": [edge.to_payload() for edge in self.edges],
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "TaskGraph":
        """Hydrate a ``TaskGraph`` from a mapping payload."""

        tasks_payload = payload.get("tasks", [])
        edges_payload = payload.get("edges", [])
        metadata_payload = payload.get("metadata", {})

        tasks: List[TaskNode] = []
        for node in tasks_payload:
            if not isinstance(node, Mapping):
                continue
            tasks.append(
                TaskNode(
                    id=str(node.get("id", "")),
                    question=str(node.get("question", "")),
                    tools=[str(tool) for tool in node.get("tools", []) or []],
                    depends_on=[
                        str(dep) for dep in node.get("depends_on", []) or []
                    ],
                    criteria=[
                        str(criterion) for criterion in node.get("criteria", []) or []
                    ],
                    affinity={
                        str(tool): float(value)
                        for tool, value in (node.get("affinity") or {}).items()
                        if _is_number(value)
                    },
                    metadata={**(node.get("metadata") or {})},
                    sub_questions=[
                        str(sub) for sub in node.get("sub_questions", []) or []
                    ]
                    or None,
                    explanation=(
                        str(node.get("explanation"))
                        if node.get("explanation") is not None
                        else None
                    ),
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

        return cls(tasks=tasks, edges=edges, metadata=metadata)


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
