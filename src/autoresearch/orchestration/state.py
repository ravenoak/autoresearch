"""State management for the dialectical reasoning process."""

import time
from collections.abc import Mapping, Sequence
from threading import RLock
from typing import TYPE_CHECKING, Any, Optional

from pydantic import BaseModel, Field, PrivateAttr

from ..agents.feedback import FeedbackEvent
from ..agents.messages import MessageProtocol
from ..models import QueryResponse

LOCK_TYPE = type(RLock())


def _default_task_graph() -> dict[str, Any]:
    """Return an empty task graph structure for planner outputs."""

    return {"tasks": [], "edges": [], "metadata": {}}


if TYPE_CHECKING:  # pragma: no cover
    from ..interfaces import QueryStateLike  # noqa: F401


class QueryState(BaseModel):
    """State object passed between agents during dialectical cycles.

    Implements :class:`~autoresearch.interfaces.QueryStateLike`.
    """

    query: str
    claims: list[dict[str, Any]] = Field(default_factory=list)
    claim_audits: list[dict[str, Any]] = Field(default_factory=list)
    sources: list[dict[str, Any]] = Field(default_factory=list)
    results: dict[str, Any] = Field(default_factory=dict)
    messages: list[dict[str, Any]] = Field(default_factory=list)
    feedback_events: list[FeedbackEvent] = Field(default_factory=list)
    coalitions: dict[str, list[str]] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    task_graph: dict[str, Any] = Field(default_factory=_default_task_graph)
    react_traces: list[dict[str, Any]] = Field(default_factory=list)
    cycle: int = 0
    primus_index: int = 0
    last_updated: float = Field(default_factory=time.time)
    error_count: int = 0

    _lock: RLock = PrivateAttr(default_factory=RLock)

    def model_post_init(self, __context: Any) -> None:  # type: ignore[override]
        """Ensure synchronization primitives survive model cloning."""
        super().model_post_init(__context)
        self._ensure_lock()

    def update(self, result: Mapping[str, object]) -> None:
        """Update state with agent result."""
        with self._lock:
            claims_obj = result.get("claims")
            if claims_obj is not None:
                if not isinstance(claims_obj, Sequence) or isinstance(
                    claims_obj, (str, bytes)
                ):
                    raise TypeError("claims must be a sequence of mappings")
                for claim in claims_obj:
                    if not isinstance(claim, Mapping):
                        raise TypeError("each claim must be a mapping")
                    claim_dict = dict(claim)
                    self.claims.append(claim_dict)
                    audit_payload = claim_dict.get("audit")
                    if isinstance(audit_payload, Mapping):
                        self.claim_audits.append(dict(audit_payload))

            sources_obj = result.get("sources")
            if sources_obj is not None:
                if not isinstance(sources_obj, Sequence) or isinstance(
                    sources_obj, (str, bytes)
                ):
                    raise TypeError("sources must be a sequence of mappings")
                for source in sources_obj:
                    if not isinstance(source, Mapping):
                        raise TypeError("each source must be a mapping")
                    self.sources.append(dict(source))

            metadata_obj = result.get("metadata")
            if metadata_obj is not None:
                if not isinstance(metadata_obj, Mapping):
                    raise TypeError("metadata must be a mapping")
                for key, value in metadata_obj.items():
                    self.metadata[key] = value
            # Update results with agent-specific outputs
            results_obj = result.get("results")
            if results_obj is not None:
                if not isinstance(results_obj, Mapping):
                    raise TypeError("results must be a mapping")
                self.results.update(results_obj)
                task_graph_obj = results_obj.get("task_graph")
                if task_graph_obj is not None:
                    self.set_task_graph(task_graph_obj)

            audits_obj = result.get("claim_audits")
            if audits_obj is not None:
                if not isinstance(audits_obj, Sequence) or isinstance(
                    audits_obj, (str, bytes)
                ):
                    raise TypeError("claim_audits must be a sequence of mappings")
                for audit in audits_obj:
                    if not isinstance(audit, Mapping):
                        raise TypeError("each claim_audit must be a mapping")
                    self.claim_audits.append(dict(audit))
            react_traces_obj = result.get("react_traces")
            if react_traces_obj is not None:
                self.extend_react_traces(react_traces_obj)
            # Update timestamp
            self.last_updated = time.time()

    def add_error(self, error_info: dict[str, Any]) -> None:
        """Track execution errors."""
        with self._lock:
            self.error_count += 1
            if "errors" not in self.metadata:
                self.metadata["errors"] = []
            self.metadata["errors"].append(error_info)

    def add_message(self, message: dict[str, Any]) -> None:
        """Store a message exchanged between agents."""
        with self._lock:
            self.messages.append(message)

    def add_feedback_event(self, event: FeedbackEvent) -> None:
        """Store a feedback event exchanged between agents."""
        with self._lock:
            self.feedback_events.append(event)

    def get_feedback_events(self, *, recipient: Optional[str] = None) -> list[FeedbackEvent]:
        """Retrieve feedback events for a specific recipient."""
        with self._lock:
            events = list(self.feedback_events)
        if recipient is not None:
            events = [e for e in events if e.target == recipient]
        return events

    def set_task_graph(self, task_graph: Any) -> None:
        """Store the structured planner output for downstream coordination."""

        with self._lock:
            normalized = self._normalise_task_graph(task_graph)
            self.task_graph = normalized
            planner_meta = self.metadata.setdefault("planner", {})
            planner_meta["task_graph"] = {
                "task_count": len(normalized.get("tasks", [])),
                "edge_count": len(normalized.get("edges", [])),
                "updated_at": time.time(),
            }

    def extend_react_traces(self, traces: Any) -> None:
        """Append a batch of ReAct traces captured during execution."""

        if isinstance(traces, Mapping):
            iterable = [traces]
        else:
            iterable = list(traces or [])

        with self._lock:
            for trace in iterable:
                if not isinstance(trace, Mapping):
                    raise TypeError("each react trace must be a mapping")
                self.react_traces.append(dict(trace))

    def add_react_trace(self, trace: Mapping[str, Any]) -> None:
        """Append a single ReAct trace entry."""

        self.extend_react_traces([trace])

    def get_react_traces(self, *, task_id: Optional[str] = None) -> list[dict[str, Any]]:
        """Retrieve ReAct traces, optionally filtered by task id."""

        with self._lock:
            traces = list(self.react_traces)
        if task_id is not None:
            traces = [trace for trace in traces if trace.get("task_id") == task_id]
        return traces

    def _normalise_task_graph(self, task_graph: Any) -> dict[str, Any]:
        """Validate and normalise a task graph payload."""

        if isinstance(task_graph, Mapping):
            payload = dict(task_graph)
        elif isinstance(task_graph, Sequence) and not isinstance(task_graph, (str, bytes)):
            payload = {"tasks": list(task_graph)}
        else:
            raise TypeError("task_graph must be a mapping or sequence")

        tasks_obj = payload.get("tasks", [])
        edges_obj = payload.get("edges", [])
        metadata_obj = payload.get("metadata", {})

        if not isinstance(tasks_obj, Sequence) or isinstance(tasks_obj, (str, bytes)):
            raise TypeError("task_graph['tasks'] must be a sequence")
        if not isinstance(edges_obj, Sequence) or isinstance(edges_obj, (str, bytes)):
            raise TypeError("task_graph['edges'] must be a sequence")
        if not isinstance(metadata_obj, Mapping):
            raise TypeError("task_graph['metadata'] must be a mapping")

        normalized_tasks: list[dict[str, Any]] = []
        for idx, task in enumerate(tasks_obj, start=1):
            if not isinstance(task, Mapping):
                raise TypeError("each task must be a mapping")
            normalized_task: dict[str, Any] = {
                "id": str(task.get("id") or f"task-{idx}"),
                "question": task.get("question")
                or task.get("goal")
                or task.get("description")
                or "",
                "tools": list(task.get("tools", [])) if task.get("tools") else [],
                "depends_on": list(task.get("depends_on", []))
                if task.get("depends_on")
                else [],
                "criteria": list(task.get("criteria", [])) if task.get("criteria") else [],
                "metadata": dict(task.get("metadata", {}))
                if isinstance(task.get("metadata"), Mapping)
                else {},
            }
            sub_questions = task.get("sub_questions")
            if isinstance(sub_questions, Sequence) and not isinstance(sub_questions, (str, bytes)):
                normalized_task["sub_questions"] = [str(value) for value in sub_questions]
            normalized_tasks.append(normalized_task)

        normalized_edges: list[dict[str, Any]] = []
        for edge in edges_obj:
            if not isinstance(edge, Mapping):
                raise TypeError("each edge must be a mapping")
            normalized_edges.append(
                {
                    "source": str(edge.get("source")),
                    "target": str(edge.get("target")),
                    "type": edge.get("type", "dependency"),
                }
            )

        metadata_copy = dict(metadata_obj)
        metadata_copy.setdefault("version", 1)

        return {"tasks": normalized_tasks, "edges": normalized_edges, "metadata": metadata_copy}

    # ------------------------------------------------------------------
    # Coalition management utilities
    # ------------------------------------------------------------------

    def add_coalition(self, name: str, members: list[str]) -> None:
        """Register a coalition of agents.

        Args:
            name: Name of the coalition
            members: Agent names that belong to the coalition
        """
        self.coalitions[name] = members

    def remove_coalition(self, name: str) -> None:
        """Remove a coalition if it exists."""
        self.coalitions.pop(name, None)

    def get_coalition_members(self, name: str) -> list[str]:
        """Return members of a coalition."""
        return self.coalitions.get(name, [])

    def get_messages(
        self,
        *,
        recipient: Optional[str] = None,
        coalition: Optional[str] = None,
        protocol: MessageProtocol | None = None,
    ) -> list[dict[str, Any]]:
        """Retrieve messages for a specific recipient or coalition."""
        with self._lock:
            messages = list(self.messages)
        if recipient is not None:
            messages = [m for m in messages if m.get("to") in (None, recipient)]
        if coalition is not None:
            members = self.coalitions.get(coalition, [])
            messages = [m for m in messages if m.get("from") in members]
        if protocol is not None:
            messages = [m for m in messages if m.get("protocol") == protocol.value]
        return messages

    def __getstate__(self) -> dict[str, Any]:
        """Drop non-serializable members before pickling."""
        try:
            state = super().__getstate__()  # type: ignore[misc]
        except AttributeError:  # pragma: no cover - legacy BaseModel fallback
            state = self.__dict__.copy()
        state.pop("_lock", None)
        private = state.get("__pydantic_private__")
        if private is not None:
            try:
                private_copy = private.copy()  # type: ignore[assignment]
            except AttributeError:  # pragma: no cover - fallback for exotic mappings
                private_copy = dict(private)
            private_copy.pop("_lock", None)
            state["__pydantic_private__"] = private_copy
        return state

    def __setstate__(self, state: dict[str, Any]) -> None:
        """Restore serialization-safe state and recreate the lock."""
        try:
            super().__setstate__(state)  # type: ignore[misc]
        except AttributeError:  # pragma: no cover - legacy BaseModel fallback
            self.__dict__.update(state)
        self._ensure_lock()

    def synthesize(self) -> QueryResponse:
        """Create final response from state."""
        # Default implementation - can be overridden by SynthesizerAgent
        return QueryResponse(
            answer=self.results.get("final_answer", "No answer synthesized"),
            citations=self.sources,
            reasoning=self.claims,
            metrics=self.metadata,
            claim_audits=self.claim_audits,
            task_graph=self.task_graph if self.task_graph.get("tasks") else None,
            react_traces=list(self.react_traces),
        )

    def get_dialectical_structure(self) -> dict[str, Any]:
        """Extract thesis, antithesis, verification, and synthesis claims."""
        structure: dict[str, Any] = {
            "thesis": None,
            "antithesis": [],
            "verification": [],
            "synthesis": None,
        }

        # Extract claims by type
        for claim in self.claims:
            claim_type = claim.get("type")
            if claim_type == "thesis":
                structure["thesis"] = claim
            elif claim_type == "antithesis":
                structure["antithesis"].append(claim)
            elif claim_type == "verification":
                structure["verification"].append(claim)
            elif claim_type == "synthesis":
                structure["synthesis"] = claim

        return structure

    def prune_context(
        self,
        max_claims: int = 50,
        max_sources: int = 20,
        max_messages: int = 50,
        max_feedback: int = 50,
    ) -> None:
        """Prune stored context to keep the state manageable.

        This method removes the oldest claims and sources when their count
        exceeds the provided limits. A summary of the number of items pruned
        is stored under ``metadata['pruned']``.

        Args:
            max_claims: Maximum number of claims to keep.
            max_sources: Maximum number of sources to keep.
        """

        with self._lock:
            pruned = {"claims": 0, "sources": 0, "messages": 0, "feedback": 0}

            if len(self.claims) > max_claims:
                excess = len(self.claims) - max_claims
                del self.claims[0:excess]
                pruned["claims"] = excess

            if len(self.sources) > max_sources:
                excess = len(self.sources) - max_sources
                del self.sources[0:excess]
                pruned["sources"] = excess

            if len(self.messages) > max_messages:
                excess = len(self.messages) - max_messages
                del self.messages[0:excess]
                pruned["messages"] = excess

            if len(self.feedback_events) > max_feedback:
                excess = len(self.feedback_events) - max_feedback
                del self.feedback_events[0:excess]
                pruned["feedback"] = excess

            if any(pruned.values()):
                self.metadata.setdefault("pruned", []).append(pruned)

    def _ensure_lock(self) -> None:
        """Guarantee the internal lock exists after serialization events."""
        lock = getattr(self, "_lock", None)
        if not isinstance(lock, LOCK_TYPE):
            object.__setattr__(self, "_lock", RLock())
