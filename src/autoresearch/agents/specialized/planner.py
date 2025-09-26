"""Planner agent for structuring complex research tasks."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from typing import Any, Dict, List

from ...agents.base import Agent, AgentRole
from ...config import ConfigModel
from ...orchestration.phases import DialoguePhase
from ...orchestration.state import QueryState
from ...logging_utils import get_logger

log = get_logger(__name__)


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
        prompt = self.generate_prompt("planner.research_plan", query=state.query)
        if getattr(config, "enable_feedback", False):
            fb = self.format_feedback(state)
            if fb:
                prompt += f"\n\nPeer feedback:\n{fb}\n"
        research_plan = adapter.generate(prompt, model=model)

        task_graph = self._generate_task_graph(research_plan, state)
        state.set_task_graph(task_graph)

        # Create and return the result
        claim = self.create_claim(research_plan, "research_plan")
        result = self.create_result(
            claims=[claim],
            metadata={
                "phase": DialoguePhase.PLANNING,
                "task_graph": {
                    "tasks": len(task_graph.get("tasks", [])),
                    "edges": len(task_graph.get("edges", [])),
                },
            },
            results={
                "research_plan": research_plan,
                "task_graph": task_graph,
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

    def _generate_task_graph(self, plan: str, state: QueryState) -> dict[str, Any]:
        """Transform LLM output into a structured task graph."""

        parsed = self._parse_json_block(plan)
        if parsed is not None:
            graph = self._normalise_parsed_payload(parsed)
        else:
            graph = self._heuristic_graph(plan)

        graph.setdefault("metadata", {})
        graph["metadata"].update(
            {
                "source": self.name,
                "cycle": state.cycle,
                "raw_plan_excerpt": plan.strip()[:5000],
            }
        )
        return graph

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

    def _normalise_parsed_payload(self, payload: Any) -> dict[str, Any]:
        """Normalise a parsed JSON payload into planner graph schema."""

        if isinstance(payload, Mapping):
            tasks_obj = payload.get("tasks")
            edges_obj = payload.get("edges")
            metadata_obj = payload.get("metadata", {})
            if isinstance(tasks_obj, Sequence):
                tasks = [self._normalise_task(task, idx) for idx, task in enumerate(tasks_obj, 1)]
            elif isinstance(payload.get("steps"), Sequence):
                tasks = [
                    self._normalise_task(task, idx)
                    for idx, task in enumerate(payload.get("steps"), 1)
                ]
            else:
                tasks = [self._normalise_task(payload, 1)]
            edges = self._normalise_edges(edges_obj, tasks)
            metadata = metadata_obj if isinstance(metadata_obj, Mapping) else {}
            return {"tasks": tasks, "edges": edges, "metadata": dict(metadata)}

        if isinstance(payload, Sequence):
            tasks = [self._normalise_task(task, idx) for idx, task in enumerate(payload, 1)]
            edges = self._normalise_edges(None, tasks)
            return {"tasks": tasks, "edges": edges, "metadata": {}}

        return self._heuristic_graph(str(payload))

    def _heuristic_graph(self, plan: str) -> dict[str, Any]:
        """Fallback graph construction using simple heuristics."""

        entries = self._split_plan_entries(plan)
        tasks = [self._normalise_task(entry, idx) for idx, entry in enumerate(entries, 1)]
        edges = self._normalise_edges(None, tasks)
        return {"tasks": tasks, "edges": edges, "metadata": {"mode": "heuristic"}}

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

    def _normalise_task(self, task: Any, index: int) -> dict[str, Any]:
        """Standardise a task payload into the task graph schema."""

        if isinstance(task, Mapping):
            question = self._extract_question(task)
            tools = self._extract_tools(task.get("tools"))
            depends_on = self._extract_sequence(task.get("depends_on"))
            criteria = self._extract_sequence(task.get("criteria"))
            sub_questions = self._extract_sequence(task.get("sub_questions"))
            metadata = (
                dict(task.get("metadata"))
                if isinstance(task.get("metadata"), Mapping)
                else {}
            )
        else:
            text = str(task).strip()
            question, tools, sub_questions, criteria = self._extract_from_text(text)
            depends_on = []
            metadata = {"source": "heuristic"}

        node: dict[str, Any] = {
            "id": str(task.get("id") if isinstance(task, Mapping) and task.get("id") else f"task-{index}"),
            "question": question,
            "tools": tools,
            "depends_on": depends_on,
            "criteria": criteria,
            "metadata": metadata,
        }
        if sub_questions:
            node["sub_questions"] = sub_questions
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
        self, edges: Any, tasks: List[dict[str, Any]]
    ) -> List[dict[str, Any]]:
        """Normalise edge payloads and include dependency edges."""

        normalized: list[dict[str, Any]] = []
        if isinstance(edges, Sequence) and not isinstance(edges, (str, bytes)):
            for edge in edges:
                if isinstance(edge, Mapping):
                    normalized.append(
                        {
                            "source": str(edge.get("source")),
                            "target": str(edge.get("target")),
                            "type": edge.get("type", "dependency"),
                        }
                    )

        for task in tasks:
            for dep in task.get("depends_on", []):
                edge = {"source": str(dep), "target": task["id"], "type": "dependency"}
                if edge not in normalized:
                    normalized.append(edge)
        return normalized
