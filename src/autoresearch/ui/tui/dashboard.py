"""Runtime support for the Textual terminal dashboard."""

from __future__ import annotations

import math
import threading
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Callable, Generator, Mapping, MutableMapping, Sequence

from ...cli_utils import VisualizationHooks
from ...models import QueryResponse
from ...monitor import _collect_system_metrics
from ...orchestration.state import QueryState
from ...orchestration.types import CallbackMap
from ...search.context import SearchContext


class DashboardUnavailableError(RuntimeError):
    """Raised when the dashboard cannot be displayed."""


@dataclass
class _DashboardState:
    """Mutable state shared between background orchestration and the UI."""

    total_loops: int
    current_loop: int = 0
    completed_loops: int = 0
    current_agent: str | None = None
    reasoning_events: list[str] | None = None
    execution_metrics: dict[str, Any] | None = None
    graph_summary: dict[str, Any] | None = None

    def record_agent(self, name: str | None) -> None:
        """Store the name of the agent that is currently running."""

        self.current_agent = name

    def record_reasoning(self, message: str) -> None:
        """Append a reasoning trace entry."""

        if self.reasoning_events is None:
            self.reasoning_events = []
        self.reasoning_events.append(message)

    def record_metrics(self, payload: Mapping[str, Any]) -> None:
        """Store execution metrics from orchestration callbacks."""

        self.execution_metrics = dict(payload)

    def record_graph_summary(self, payload: Mapping[str, Any]) -> None:
        """Store the latest knowledge-graph summary."""

        self.graph_summary = dict(payload)


def _safe_graph_summary() -> dict[str, Any]:
    """Return a defensive copy of the latest graph summary."""

    try:
        summary = SearchContext.get_instance().get_graph_summary()
    except Exception:
        return {}
    return dict(summary)


def _coerce_reasoning_snippet(
    agent_name: str,
    result: Mapping[str, Any] | None,
    state: QueryState,
) -> str:
    """Derive a short textual snippet describing the agent outcome."""

    snippet: str | None = None
    if result:
        raw_summary = result.get("summary")
        if isinstance(raw_summary, str) and raw_summary.strip():
            snippet = raw_summary.strip()
        elif isinstance(raw_summary, Mapping):
            description = raw_summary.get("description")
            if isinstance(description, str) and description.strip():
                snippet = description.strip()
        if snippet is None:
            raw_thought = result.get("thought")
            if isinstance(raw_thought, str) and raw_thought.strip():
                snippet = raw_thought.strip()
    if snippet is None:
        try:
            claims: Sequence[Mapping[str, Any]] = list(state.claims)
        except Exception:
            claims = []
        if claims:
            last_claim = claims[-1]
            text_fields = (
                str(last_claim.get("text") or last_claim.get("claim") or "").strip()
            )
            if text_fields:
                snippet = text_fields
    if snippet is None and result:
        answer = result.get("answer")
        if isinstance(answer, str) and answer.strip():
            snippet = answer.strip()
    if not snippet:
        snippet = "completed without additional reasoning"
    snippet = snippet.replace("\n", " ")
    if len(snippet) > 180:
        snippet = snippet[:177] + "..."
    return f"[b]{agent_name}[/b]: {snippet}"


def _format_summary_table(summary: Mapping[str, Any]) -> str:
    """Format a nested dictionary into a readable block."""

    if not summary:
        return "No knowledge-graph summary available yet."
    lines: list[str] = []
    for key, value in sorted(summary.items()):
        if isinstance(value, Mapping):
            lines.append(f"[b]{key}[/b]:")
            for sub_key, sub_value in sorted(value.items()):
                lines.append(f"  {sub_key}: {sub_value}")
        else:
            lines.append(f"[b]{key}[/b]: {value}")
    return "\n".join(lines)


def _format_metrics_table(
    system_metrics: Mapping[str, Any],
    execution_metrics: Mapping[str, Any] | None,
) -> str:
    """Render system and orchestration metrics as a simple text table."""

    rows: list[str] = []
    if execution_metrics:
        rows.append("[b]Orchestration[/b]")
        for key, value in sorted(execution_metrics.items()):
            rows.append(f"  {key}: {value}")
    if system_metrics:
        rows.append("[b]System[/b]")
        for key, value in sorted(system_metrics.items()):
            if isinstance(value, float):
                rounded_value: Any = "nan" if math.isnan(value) else f"{value:.2f}"
            elif isinstance(value, int):
                rounded_value = value
            else:
                rounded_value = value
            rows.append(f"  {key}: {rounded_value}")
    if not rows:
        return "No metrics available yet."
    return "\n".join(rows)


@contextmanager
def _subscribe_visualization_hooks(
    hooks: VisualizationHooks,
    callback: Callable[[], None],
) -> Generator[None, None, None]:
    """Attach a callback to visualization hooks and restore them afterwards."""

    original_visualize = hooks.visualize
    original_visualize_query = hooks.visualize_query

    def _wrapped_visualize(*args: Any, **kwargs: Any) -> Any:
        try:
            return original_visualize(*args, **kwargs)
        finally:
            callback()

    def _wrapped_visualize_query(*args: Any, **kwargs: Any) -> Any:
        try:
            return original_visualize_query(*args, **kwargs)
        finally:
            callback()

    hooks.visualize = _wrapped_visualize
    hooks.visualize_query = _wrapped_visualize_query
    try:
        yield
    finally:
        hooks.visualize = original_visualize
        hooks.visualize_query = original_visualize_query


class _DashboardAppBase:
    """Helper mixin defining shared update methods for the Textual app."""

    def __init__(self, state: _DashboardState) -> None:
        self._state = state
        self._system_metrics: dict[str, Any] = {}
        self._lock = threading.Lock()

    def update_cycle(self, *, loop: int, agent: str | None = None) -> None:
        """Record the currently active loop and agent."""

        with self._lock:
            self._state.current_loop = loop
            self._state.record_agent(agent)

    def complete_cycle(
        self,
        *,
        loop: int,
        metrics: Mapping[str, Any] | None,
        summary: Mapping[str, Any] | None,
    ) -> None:
        """Record completion of a loop along with metrics and graph summary."""

        with self._lock:
            self._state.completed_loops = max(self._state.completed_loops, loop + 1)
            if metrics:
                self._state.record_metrics(metrics)
            if summary:
                self._state.record_graph_summary(summary)

    def append_reasoning(self, entry: str) -> None:
        """Append a reasoning entry to the shared state."""

        with self._lock:
            self._state.record_reasoning(entry)

    def snapshot_state(self) -> _DashboardState:
        """Return a copy of the current dashboard state."""

        with self._lock:
            snapshot = _DashboardState(
                total_loops=self._state.total_loops,
                current_loop=self._state.current_loop,
                completed_loops=self._state.completed_loops,
                current_agent=self._state.current_agent,
            )
            if self._state.reasoning_events:
                snapshot.reasoning_events = list(self._state.reasoning_events)
            if self._state.execution_metrics:
                snapshot.execution_metrics = dict(self._state.execution_metrics)
            if self._state.graph_summary:
                snapshot.graph_summary = dict(self._state.graph_summary)
            return snapshot

    def refresh_system_metrics(self) -> None:
        """Collect system metrics using the monitor utilities."""

        self._system_metrics = _collect_system_metrics()


def run_dashboard(
    *,
    runner: Callable[[CallbackMap], QueryResponse],
    total_loops: int,
    hooks: VisualizationHooks,
) -> QueryResponse:
    """Launch the Textual dashboard and execute ``runner`` within it."""

    try:
        from textual.app import App, ComposeResult
        from textual.containers import Grid
        from textual.widgets import Footer, Header, RichLog, Static
    except ModuleNotFoundError as exc:  # pragma: no cover - import guard
        raise DashboardUnavailableError(
            "Textual is not installed. Install the 'autoresearch[tui]' extra to enable the "
            "dashboard."
        ) from exc

    state = _DashboardState(total_loops=total_loops)
    mixin = _DashboardAppBase(state)

    class DashboardApp(App[QueryResponse | None]):  # type: ignore[misc]
        """Textual application showing live orchestration telemetry."""

        CSS = """
        Screen {
            layout: vertical;
        }
        #dashboard {
            layout: grid;
            grid-size: 2 2;
            grid-columns: 1fr 1fr;
            grid-rows: 1fr 1fr;
            gap: 1;
            padding: 1;
        }
        .panel {
            border: solid green;
            padding: 1;
        }
        #reasoning {
            overflow: scroll;
        }
        """

        BINDINGS = [("q", "quit", "Quit dashboard")]

        def __init__(self) -> None:
            super().__init__()
            self._state = mixin
            self._result: QueryResponse | None = None
            self._error: BaseException | None = None

        def compose(self) -> ComposeResult:
            yield Header()
            with Grid(id="dashboard"):
                yield Static("", id="progress", classes="panel")
                yield RichLog(id="reasoning", classes="panel")
                yield Static("", id="metrics", classes="panel")
                yield Static("", id="graph", classes="panel")
            yield Footer()

        def on_mount(self) -> None:
            self._progress = self.query_one("#progress", Static)
            self._metrics = self.query_one("#metrics", Static)
            self._graph = self.query_one("#graph", Static)
            self._reasoning = self.query_one("#reasoning", RichLog)
            self._state.refresh_system_metrics()
            self._render_progress()
            self._update_metrics()
            self._update_graph({})
            self.set_interval(1.5, self._poll_metrics)
            self.call_in_thread(self._run)

        def _run(self) -> None:
            callbacks: MutableMapping[str, Callable[..., Any]] = {}

            def _refresh_graph() -> None:
                summary = _safe_graph_summary()
                self.call_from_thread(self._update_graph, summary)

            def _cycle_start(loop: int, state_obj: QueryState) -> None:
                self._state.update_cycle(loop=loop, agent=None)
                self.call_from_thread(self._render_progress)

            def _cycle_end(loop: int, state_obj: QueryState) -> None:
                metrics = {}
                meta = getattr(state_obj, "metadata", {})
                if isinstance(meta, Mapping):
                    execution = meta.get("execution_metrics")
                    if isinstance(execution, Mapping):
                        metrics = dict(execution)
                summary = _safe_graph_summary()
                self._state.complete_cycle(loop=loop, metrics=metrics, summary=summary)
                self.call_from_thread(self._render_progress)
                self.call_from_thread(self._update_metrics)
                self.call_from_thread(self._update_graph, summary)

            def _agent_start(agent_name: str, state_obj: QueryState) -> None:
                self._state.update_cycle(loop=state_obj.cycle, agent=agent_name)
                self.call_from_thread(self._render_progress)

            def _agent_end(
                agent_name: str,
                result: Mapping[str, Any] | None,
                state_obj: QueryState,
            ) -> None:
                entry = _coerce_reasoning_snippet(agent_name, result, state_obj)
                self._state.append_reasoning(entry)
                self.call_from_thread(self._append_reasoning, entry)

            callbacks["on_cycle_start"] = _cycle_start
            callbacks["on_cycle_end"] = _cycle_end
            callbacks["on_agent_start"] = _agent_start
            callbacks["on_agent_end"] = _agent_end

            try:
                with _subscribe_visualization_hooks(hooks, _refresh_graph):
                    result = runner(callbacks)
            except BaseException as exc:  # pragma: no cover - defensive guard
                self._error = exc
                self.call_from_thread(self._abort)
                return
            self._result = result
            self.call_from_thread(self._finish)

        def _abort(self) -> None:
            self._render_progress()
            self.exit(None)

        def _finish(self) -> None:
            snapshot = self._state.snapshot_state()
            self._update_metrics()
            self._update_graph(snapshot.graph_summary or {})
            self.exit(self._result)

        def _poll_metrics(self) -> None:
            self._state.refresh_system_metrics()
            self._update_metrics()

        def _render_progress(self) -> None:
            snapshot = self._state.snapshot_state()
            completed = snapshot.completed_loops
            total = max(snapshot.total_loops, 1)
            indicators = []
            for index in range(total):
                indicators.append("■" if index < completed else "□")
            agent = snapshot.current_agent or "idle"
            self._progress.update(
                "\n".join(
                    [
                        "[b]Cycle Progress[/b]",
                        f"Loop {completed}/{total}",
                        "".join(indicators),
                        f"Agent: {agent}",
                    ]
                )
            )

        def _update_metrics(self) -> None:
            snapshot = self._state.snapshot_state()
            content = _format_metrics_table(
                mixin._system_metrics,
                snapshot.execution_metrics,
            )
            self._metrics.update(f"[b]Metrics[/b]\n{content}")

        def _update_graph(self, summary: Mapping[str, Any]) -> None:
            formatted = _format_summary_table(summary)
            self._graph.update(f"[b]Knowledge Graph[/b]\n{formatted}")

        def _append_reasoning(self, entry: str) -> None:
            self._reasoning.write(entry)

        @property
        def error(self) -> BaseException | None:
            """Return the orchestration error, if any."""

            return self._error

    app = DashboardApp()
    result = app.run()
    if app.error is not None:
        raise DashboardUnavailableError(
            "Dashboard terminated because orchestration raised an exception."
        ) from app.error
    if result is None:
        raise DashboardUnavailableError("Dashboard exited without producing a result.")
    return result  # type: ignore[no-any-return]
