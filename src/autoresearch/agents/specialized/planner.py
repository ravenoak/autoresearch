"""Planner agent for structuring complex research tasks."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from textwrap import dedent
from collections.abc import Mapping, Sequence
from typing import Any, Dict, List, Tuple

from ...agents.base import Agent, AgentRole
from ...config import ConfigModel
from ...orchestration.phases import DialoguePhase
from ...orchestration.state import QueryState
from ...orchestration.task_graph import TaskEdge, TaskGraph, TaskNode
from ...logging_utils import get_logger
from ...search.context import SearchContext

log = get_logger(__name__)


@dataclass(slots=True)
class PlannerPromptBuilder:
    """Compose a planner prompt that enforces structured JSON output."""

    base_prompt: str
    query: str
    feedback: str | None = None
    existing_graph: Mapping[str, Any] | None = None
    graph_context: Mapping[str, Any] | None = None
    include_schema_notes: bool = True
    _schema: dict[str, Any] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        """Initialise the JSON schema shared with the language model."""

        self._schema = {
            "type": "object",
            "required": ["tasks", "edges", "metadata"],
            "properties": {
                "objectives": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Shared research goals across the plan.",
                },
                "exit_criteria": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Signals that confirm the plan is complete.",
                },
                "tasks": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["id", "question"],
                        "properties": {
                            "id": {"type": "string"},
                            "question": {"type": "string"},
                            "objectives": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                            "tools": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                            "tool_affinity": {
                                "type": "object",
                                "additionalProperties": {
                                    "type": "number",
                                },
                            },
                            "depends_on": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                            "exit_criteria": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                            "explanation": {"type": "string"},
                        },
                    },
                },
                "edges": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["source", "target"],
                        "properties": {
                            "source": {"type": "string"},
                            "target": {"type": "string"},
                            "type": {
                                "type": "string",
                                "enum": ["dependency", "related", "evidence"],
                            },
                        },
                    },
                },
                "metadata": {
                    "type": "object",
                    "properties": {
                        "version": {"type": "integer"},
                        "notes": {"type": "string"},
                    },
                },
            },
        }

    def build(self) -> str:
        """Return the final planner prompt with JSON schema guidance."""

        sections: list[str] = [self.base_prompt.strip()]
        if self.include_schema_notes:
            schema_text = json.dumps(self._schema, indent=2, sort_keys=True)
            notes = dedent(
                """
                You must respond with JSON that validates against the schema below.
                - Populate ``objectives`` with decomposed questions for each task.
                - Store numeric tool scores in ``tool_affinity`` with values in ``[0, 1]``.
                - Provide concrete "exit_criteria" that confirm completion.
                - Summarise rationale for the task in "explanation".
                - Avoid prose outside the JSON object.
                """
            ).strip()
            sections.append(notes)
            sections.append(schema_text)

        if self.existing_graph and self.existing_graph.get("tasks"):
            prior_summary = json.dumps(self.existing_graph, indent=2)[:2000]
            sections.append(
                "Current task graph context (truncate to stay concise):\n"
                f"{prior_summary}"
            )

        if self.graph_context:
            graph_section = self._format_graph_context(self.graph_context)
            if graph_section:
                sections.append(graph_section)

        if self.feedback:
            sections.append(f"Peer feedback:\n{self.feedback.strip()}")

        return "\n\n".join(section for section in sections if section).strip()

    @staticmethod
    def _format_float(value: Any) -> str:
        try:
            return f"{float(value):.2f}"
        except (TypeError, ValueError):
            return "0.00"

    def _format_graph_context(self, context: Mapping[str, Any]) -> str:
        """Return a compact textual summary of knowledge graph signals."""

        sections: list[str] = []

        similarity = context.get("similarity")
        if isinstance(similarity, Mapping):
            weighted = self._format_float(similarity.get("weighted_score"))
            raw = self._format_float(similarity.get("raw_score"))
            sections.append(
                f"- Graph similarity support: {weighted} (raw {raw})"
            )

        contradictions = context.get("contradictions")
        if isinstance(contradictions, Mapping):
            weighted = self._format_float(contradictions.get("weighted_score"))
            raw = self._format_float(contradictions.get("raw_score"))
            sections.append(
                f"- Contradiction score: {weighted} (raw {raw})"
            )
            items = contradictions.get("items")
            if isinstance(items, Sequence):
                entries = [item for item in items if isinstance(item, Mapping)]
                preview = entries[:3]
                if preview:
                    sections.append("  Contradictory findings:")
                    for item in preview:
                        subject = str(item.get("subject") or "?")
                        predicate = str(item.get("predicate") or "?")
                        objects = item.get("objects")
                        if isinstance(objects, Sequence) and objects:
                            object_preview = ", ".join(
                                str(obj) for obj in list(objects)[:3]
                            )
                            if len(objects) > 3:
                                object_preview += ", …"
                        else:
                            object_preview = "?"
                        sections.append(
                            f"    - {subject} --{predicate}--> {object_preview}"
                        )
                    remaining = len(entries) - len(preview)
                    if remaining > 0:
                        sections.append(f"    - … ({remaining} more)")

        neighbors = context.get("neighbors")
        if isinstance(neighbors, Mapping):
            neighbour_lines: list[str] = []
            for entity, edges in neighbors.items():
                if len(neighbour_lines) >= 3:
                    break
                if not isinstance(edges, Sequence):
                    continue
                for edge in edges:
                    if len(neighbour_lines) >= 3:
                        break
                    if not isinstance(edge, Mapping):
                        continue
                    predicate = str(edge.get("predicate") or edge.get("relation") or "?")
                    target = str(edge.get("target") or edge.get("object") or "?")
                    direction = edge.get("direction")
                    if direction == "in":
                        arrow = "←"
                    elif direction == "both":
                        arrow = "↔"
                    else:
                        arrow = "→"
                    neighbour_lines.append(
                        f"  - {entity} {arrow} ({predicate}) {target}"
                    )
            if neighbour_lines:
                sections.append("- Representative neighbours:")
                sections.extend(neighbour_lines)

        paths = context.get("paths")
        if isinstance(paths, Sequence):
            formatted_paths: list[str] = []
            total_paths = 0
            for path in paths:
                if not isinstance(path, Sequence):
                    continue
                nodes = [str(node) for node in path if node]
                if not nodes:
                    continue
                total_paths += 1
                if len(formatted_paths) < 3:
                    formatted_paths.append(" → ".join(nodes))
            if formatted_paths:
                sections.append("- Multi-hop paths:")
                for item in formatted_paths:
                    sections.append(f"  - {item}")
                if total_paths > len(formatted_paths):
                    sections.append("  - …")

        sources = context.get("sources")
        if isinstance(sources, Sequence):
            parsed_sources = [
                str(source).strip()
                for source in sources
                if isinstance(source, str) and source.strip()
            ]
            if parsed_sources:
                preview_sources = parsed_sources[:5]
                source_line = ", ".join(preview_sources)
                if len(parsed_sources) > len(preview_sources):
                    source_line += ", …"
                sections.append(f"- Provenance sources: {source_line}")

        provenance = context.get("provenance")
        if isinstance(provenance, Sequence):
            count = len([item for item in provenance if isinstance(item, Mapping)])
            if count:
                sections.append(f"- Provenance records analysed: {count}")

        if not sections:
            return ""
        header = "Knowledge graph signals:"
        return "\n".join([header, *sections])


class PlannerAgent(Agent):
    """Structures complex research tasks into organized plans."""

    role: AgentRole = AgentRole.SPECIALIST
    name: str = "Planner"

    def execute(self, state: QueryState, config: ConfigModel) -> Dict[str, Any]:
        """Create a structured research plan for the query."""
        log.info(f"PlannerAgent executing (cycle {state.cycle})")

        adapter = self.get_adapter(config)
        model = self.get_model(config)

        # Generate a research plan using the prompt template
        base_prompt = self.generate_prompt("planner.research_plan", query=state.query)
        feedback = None
        if getattr(config, "enable_feedback", False):
            feedback = self.format_feedback(state) or None
        graph_context: Mapping[str, Any] | None = None
        context_cfg = getattr(config.search, "context_aware", None)
        if getattr(context_cfg, "planner_graph_conditioning", False):
            try:
                search_context = SearchContext.get_instance()
                graph_metadata = search_context.get_graph_stage_metadata()
                graph_summary = search_context.get_graph_summary()
            except Exception:
                graph_metadata = {}
                graph_summary = {}
            payload: dict[str, Any] = {}
            if isinstance(graph_metadata, Mapping):
                for key in ("contradictions", "similarity", "neighbors", "paths"):
                    value = graph_metadata.get(key)
                    if value:
                        payload[key] = value
            if isinstance(graph_summary, Mapping):
                for key in ("sources", "provenance"):
                    value = graph_summary.get(key)
                    if value:
                        payload[key] = value
            if payload:
                graph_context = payload

        prompt = PlannerPromptBuilder(
            base_prompt=base_prompt,
            query=state.query,
            feedback=feedback,
            existing_graph=state.task_graph if state.task_graph.get("tasks") else None,
            graph_context=graph_context,
        ).build()
        research_plan = adapter.generate(prompt, model=model)

        task_graph, planner_warnings = self._generate_task_graph(research_plan, state)
        normalization_warnings = state.set_task_graph(task_graph)
        state.record_planner_trace(
            prompt=prompt,
            raw_response=research_plan,
            normalized=state.task_graph,
            warnings=[*planner_warnings, *normalization_warnings],
        )
        task_graph_payload = task_graph.to_payload()

        # Create and return the result
        claim = self.create_claim(research_plan, "research_plan")
        result = self.create_result(
            claims=[claim],
            metadata={
                "phase": DialoguePhase.PLANNING,
                "task_graph": {
                    "tasks": len(task_graph_payload.get("tasks", [])),
                    "edges": len(task_graph_payload.get("edges", [])),
                },
            },
            results={
                "research_plan": research_plan,
                "task_graph": task_graph_payload,
            },
        )

        if getattr(config, "enable_agent_messages", False):
            if state.coalitions:
                for c, m in state.coalitions.items():
                    if self.name in m:
                        self.broadcast(
                            state,
                            f"Planning complete in cycle {state.cycle}",
                            coalition=c,
                        )
            else:
                self.send_message(state, "Planning complete")

        return result

    def can_execute(self, state: QueryState, config: ConfigModel) -> bool:
        """Best executed at the beginning of the research process."""
        # The Planner is most useful at the beginning of the process
        # or when there are no existing claims
        is_beginning = state.cycle == 0 or len(state.claims) == 0
        return super().can_execute(state, config) and is_beginning

    # ------------------------------------------------------------------
    # Task graph generation helpers
    # ------------------------------------------------------------------

    def _generate_task_graph(
        self, plan: str, state: QueryState
    ) -> Tuple[TaskGraph, List[dict[str, Any]]]:
        """Transform LLM output into a structured task graph."""

        warnings: List[dict[str, Any]] = []
        parsed = self._parse_json_block(plan)
        if parsed is not None:
            graph = self._normalise_parsed_payload(parsed, warnings)
        else:
            warnings.append(
                self._planner_warning(
                    "planner.missing_json",
                    "LLM output did not include structured JSON; applied heuristic",
                    detail={"excerpt": plan.strip()[:200]},
                )
            )
            graph = self._heuristic_graph(plan, warnings)

        graph.metadata.setdefault("source", self.name)
        graph.metadata.update(
            {
                "cycle": state.cycle,
                "raw_plan_excerpt": plan.strip()[:5000],
            }
        )
        return graph, warnings

    def _parse_json_block(self, plan: str) -> Any:
        """Attempt to parse a JSON block from the planner output."""

        candidates: List[str] = []
        stripped = plan.strip()
        if stripped:
            candidates.append(stripped)
        fence_pattern = re.compile(r"```(?:json)?\s*(.*?)```", re.IGNORECASE | re.DOTALL)
        candidates.extend(match.group(1).strip() for match in fence_pattern.finditer(plan))

        for candidate in candidates:
            if not candidate:
                continue
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                continue
        return None

    def _normalise_parsed_payload(
        self, payload: Any, warnings: List[dict[str, Any]]
    ) -> TaskGraph:
        """Normalise a parsed JSON payload into planner graph schema."""

        if isinstance(payload, Mapping):
            tasks_obj = payload.get("tasks")
            edges_obj = payload.get("edges")
            metadata_obj = payload.get("metadata", {})
            if isinstance(tasks_obj, Sequence) and not isinstance(tasks_obj, (str, bytes)):
                task_items = list(tasks_obj)
                tasks = [
                    self._normalise_task(task, idx, warnings)
                    for idx, task in enumerate(task_items, 1)
                ]
            else:
                steps_obj = payload.get("steps")
                if isinstance(steps_obj, Sequence) and not isinstance(steps_obj, (str, bytes)):
                    step_items = list(steps_obj)
                    tasks = [
                        self._normalise_task(task, idx, warnings)
                        for idx, task in enumerate(step_items, 1)
                    ]
                else:
                    tasks = [self._normalise_task(payload, 1, warnings)]
            edges_source = (
                edges_obj
                if isinstance(edges_obj, Sequence) and not isinstance(edges_obj, (str, bytes))
                else []
            )
            metadata_source = metadata_obj if isinstance(metadata_obj, Mapping) else {}
            edges = self._normalise_edges(edges_source, tasks, warnings)
            metadata = dict(metadata_source)
            return TaskGraph(tasks=tasks, edges=edges, metadata=metadata)

        if isinstance(payload, Sequence) and not isinstance(payload, (str, bytes)):
            seq_items = list(payload)
            tasks = [
                self._normalise_task(task, idx, warnings)
                for idx, task in enumerate(seq_items, 1)
            ]
            edges = self._normalise_edges([], tasks, warnings)
            return TaskGraph(tasks=tasks, edges=edges, metadata={})

        warnings.append(
            self._planner_warning(
                "planner.unsupported_payload",
                "Planner output shape unsupported; fallback to heuristics",
            )
        )
        return self._heuristic_graph(str(payload), warnings)

    def _heuristic_graph(
        self, plan: str, warnings: List[dict[str, Any]]
    ) -> TaskGraph:
        """Fallback graph construction using simple heuristics."""

        entries = self._split_plan_entries(plan)
        tasks = [
            self._normalise_task(entry, idx, warnings)
            for idx, entry in enumerate(entries, 1)
        ]
        edges = self._normalise_edges(None, tasks, warnings)
        return TaskGraph(
            tasks=tasks,
            edges=edges,
            metadata={"mode": "heuristic"},
        )

    def _split_plan_entries(self, plan: str) -> List[Any]:
        """Split plan text into task-sized segments."""

        bullet_pattern = re.compile(r"^\s*(?:[-*]|\d+[.)])\s+", re.MULTILINE)
        segments = [segment.strip() for segment in bullet_pattern.split(plan) if segment.strip()]
        if segments:
            return segments

        paragraphs = [block.strip() for block in plan.split("\n\n") if block.strip()]
        if paragraphs:
            return paragraphs

        return [plan.strip()] if plan.strip() else []

    def _normalise_task(
        self, task: Any, index: int, warnings: List[dict[str, Any]]
    ) -> TaskNode:
        """Standardise a task payload into the task graph schema."""

        task_id = f"task-{index}"
        sub_questions: List[str] = []
        explanation: str | None = None

        if isinstance(task, Mapping):
            raw_id = task.get("id")
            if raw_id:
                task_id = str(raw_id)
            else:
                warnings.append(
                    self._planner_warning(
                        "planner.generated_id",
                        "Task missing identifier; generated placeholder.",
                        task_index=index,
                    )
                )
            question = self._extract_question(task)
            tools = self._extract_tools(task.get("tools"))
            depends_on = self._extract_sequence(task.get("depends_on"))
            criteria = self._extract_sequence(
                task.get("criteria") or task.get("exit_criteria")
            )
            sub_questions = self._extract_sequence(
                task.get("sub_questions") or task.get("objectives")
            )
            affinity = self._extract_affinity(
                task.get("affinity") or task.get("tool_affinity"),
                warnings,
                task_id=task_id,
                task_index=index,
            )
            metadata_payload = task.get("metadata")
            if isinstance(metadata_payload, Mapping):
                metadata = dict(metadata_payload)
            else:
                if metadata_payload not in (None, {}):
                    warnings.append(
                        self._planner_warning(
                            "planner.metadata_invalid",
                            "Task metadata payload must be a mapping.",
                            task_id=task_id,
                            task_index=index,
                            detail={"metadata": metadata_payload},
                        )
                    )
                metadata = {}
            explanation_value = task.get("explanation")
            if isinstance(explanation_value, str):
                explanation = explanation_value.strip() or None
            if not question:
                warnings.append(
                    self._planner_warning(
                        "planner.missing_question",
                        "Task is missing question text.",
                        task_id=task_id,
                        task_index=index,
                    )
                )
        else:
            text = str(task).strip()
            question, tools, sub_questions, criteria = self._extract_from_text(text)
            depends_on = []
            affinity = {}
            metadata = {"source": "heuristic"}
            if not question:
                warnings.append(
                    self._planner_warning(
                        "planner.heuristic_empty",
                        "Heuristic parsing produced an empty question.",
                        task_index=index,
                    )
                )

        node = TaskNode(
            id=task_id,
            question=question,
            tools=tools,
            depends_on=depends_on,
            criteria=criteria,
            affinity=affinity,
            metadata=metadata,
            sub_questions=sub_questions or None,
            explanation=explanation,
        )
        return node

    def _extract_question(self, task: Mapping[str, Any]) -> str:
        for key in ("question", "goal", "prompt", "description", "task"):
            value = task.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return ""

    def _extract_tools(self, tools: Any) -> List[str]:
        if isinstance(tools, Mapping):
            return [str(name).strip() for name in tools.keys() if str(name).strip()]
        if isinstance(tools, Sequence) and not isinstance(tools, (str, bytes)):
            return [str(tool).strip() for tool in tools if str(tool).strip()]
        if isinstance(tools, str):
            return [segment.strip() for segment in re.split(r",|/|;| and ", tools) if segment.strip()]
        return []

    def _extract_sequence(self, value: Any) -> List[str]:
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
            return [str(item).strip() for item in value if str(item).strip()]
        if isinstance(value, str):
            return [segment.strip() for segment in re.split(r",|;|/", value) if segment.strip()]
        return []

    def _extract_affinity(
        self,
        affinity: Any,
        warnings: List[dict[str, Any]],
        *,
        task_id: str,
        task_index: int,
    ) -> Dict[str, float]:
        """Extract tool affinity scores as a numeric mapping."""

        cleaned: Dict[str, float] = {}
        if affinity is None:
            return cleaned

        if isinstance(affinity, Mapping):
            for tool, value in affinity.items():
                try:
                    cleaned[str(tool)] = float(value)
                except (TypeError, ValueError):
                    warnings.append(
                        self._planner_warning(
                            "planner.affinity_cast_failed",
                            "Failed to cast affinity score to float.",
                            task_id=task_id,
                            task_index=task_index,
                            detail={"tool": str(tool), "value": value},
                        )
                    )
            return cleaned

        if isinstance(affinity, str):
            tokens = [chunk.strip() for chunk in re.split(r",|;", affinity) if chunk.strip()]
            return self._extract_affinity(tokens, warnings, task_id=task_id, task_index=task_index)

        if isinstance(affinity, Sequence) and not isinstance(affinity, (str, bytes)):
            for entry in affinity:
                if isinstance(entry, Mapping):
                    nested = self._extract_affinity(
                        entry,
                        warnings,
                        task_id=task_id,
                        task_index=task_index,
                    )
                    for tool, value in nested.items():
                        cleaned.setdefault(tool, value)
                elif isinstance(entry, Sequence) and len(entry) == 2:
                    tool, value = entry
                    try:
                        cleaned[str(tool)] = float(value)
                    except (TypeError, ValueError):
                        warnings.append(
                            self._planner_warning(
                                "planner.affinity_cast_failed",
                                "Failed to cast affinity tuple score to float.",
                                task_id=task_id,
                                task_index=task_index,
                                detail={"tool": str(tool), "value": value},
                            )
                        )
                elif isinstance(entry, str):
                    if ":" in entry:
                        tool, score = entry.split(":", 1)
                    elif "=" in entry:
                        tool, score = entry.split("=", 1)
                    else:
                        warnings.append(
                            self._planner_warning(
                                "planner.affinity_unparsed",
                                "Affinity string entry missing delimiter.",
                                task_id=task_id,
                                task_index=task_index,
                                detail={"entry": entry},
                            )
                        )
                        continue
                    try:
                        cleaned[tool.strip()] = float(score.strip())
                    except (TypeError, ValueError):
                        warnings.append(
                            self._planner_warning(
                                "planner.affinity_cast_failed",
                                "Failed to cast affinity string score to float.",
                                task_id=task_id,
                                task_index=task_index,
                                detail={"tool": tool.strip(), "value": score},
                            )
                        )
                else:
                    warnings.append(
                        self._planner_warning(
                            "planner.affinity_unparsed",
                            "Unsupported affinity entry type.",
                            task_id=task_id,
                            task_index=task_index,
                            detail={"entry": entry},
                        )
                    )
            return cleaned

        warnings.append(
            self._planner_warning(
                "planner.affinity_unparsed",
                "Unsupported affinity payload type.",
                task_id=task_id,
                task_index=task_index,
                detail={"affinity": affinity},
            )
        )
        return cleaned

    def _extract_from_text(self, text: str) -> tuple[str, List[str], List[str], List[str]]:
        """Extract question, tools, and sub-questions from raw text."""

        tools: List[str] = []
        sub_questions: List[str] = []
        criteria: List[str] = []

        tools_match = re.search(r"Tools?:\s*(.+)", text, flags=re.IGNORECASE)
        if tools_match:
            tools = self._extract_tools(tools_match.group(1))
            text = text[: tools_match.start()].strip()

        sub_match = re.search(r"Sub-?questions?:\s*(.+)", text, flags=re.IGNORECASE)
        if sub_match:
            sub_questions = self._extract_sequence(sub_match.group(1))
            text = text[: sub_match.start()].strip()

        criteria_match = re.search(r"Criteria:?\s*(.+)", text, flags=re.IGNORECASE)
        if criteria_match:
            criteria = self._extract_sequence(criteria_match.group(1))
            text = text[: criteria_match.start()].strip()

        question = text.split(". ")[0].strip() if text else ""
        return question, tools, sub_questions, criteria

    def _normalise_edges(
        self, edges: Any, tasks: List[TaskNode], warnings: List[dict[str, Any]]
    ) -> List[TaskEdge]:
        """Normalise edge payloads and include dependency edges."""

        normalized: list[TaskEdge] = []
        if isinstance(edges, Sequence) and not isinstance(edges, (str, bytes)):
            for edge in edges:
                if isinstance(edge, Mapping):
                    normalized.append(
                        TaskEdge(
                            source=str(edge.get("source")),
                            target=str(edge.get("target")),
                            type=str(edge.get("type", "dependency")),
                        )
                    )
                else:
                    warnings.append(
                        self._planner_warning(
                            "planner.invalid_edge",
                            "Edge payload must be a mapping.",
                            detail={"edge": edge},
                        )
                    )

        existing = {(edge.source, edge.target, edge.type) for edge in normalized}
        for task in tasks:
            for dep in task.depends_on:
                signature = (dep, task.id, "dependency")
                if signature not in existing:
                    normalized.append(TaskEdge(source=dep, target=task.id))
                    existing.add(signature)
        return normalized

    def _planner_warning(
        self,
        code: str,
        message: str,
        *,
        task_id: str | None = None,
        task_index: int | None = None,
        detail: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a structured warning entry for planner telemetry."""

        payload: dict[str, Any] = {"code": code, "message": message}
        if task_id is not None:
            payload["task_id"] = task_id
        if task_index is not None:
            payload["task_index"] = task_index
        if detail is not None:
            payload["detail"] = dict(detail)
        return payload
