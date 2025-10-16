"""Interactive monitoring commands for Autoresearch."""

from __future__ import annotations

import sys
import time
from typing import Any, Dict, List, Union

from rich.console import Console
from rich.live import Live
from rich.progress import Progress
from rich.table import Table
from rich.tree import Tree
import typer


from ..config.loader import ConfigLoader
from ..logging_utils import get_logger
from ..orchestration import metrics as orch_metrics
from ..orchestration.orchestrator import Orchestrator
from ..orchestration.reasoning_payloads import normalize_reasoning_step
from ..orchestration.state import QueryState
from ..output_format import OutputFormatter
from ..resource_monitor import ResourceMonitor
from .node_health import NodeHealthMonitor
from .system_monitor import SystemMonitor
from .telemetry import (
    AUDIT_TELEMETRY_FIELDS,
    build_audit_telemetry,
    normalize_audit_payload,
)

monitor_app = typer.Typer(help="Monitoring utilities")

_loader = ConfigLoader()
_system_monitor: SystemMonitor | None = None

__all__ = [
    "SystemMonitor",
    "NodeHealthMonitor",
    "AUDIT_TELEMETRY_FIELDS",
    "build_audit_telemetry",
    "normalize_audit_payload",
]
log = get_logger(__name__)


@monitor_app.callback()
def init_metrics(ctx: typer.Context) -> None:  # pragma: no cover - simple hook
    """Initialize counters before executing monitor commands."""
    orch_metrics.ensure_counters_initialized()


def _calculate_health(cpu: float, mem: float) -> str:
    config = _loader.load_config()
    cpu_crit = getattr(config, "cpu_critical_threshold", 90)
    mem_crit = getattr(config, "memory_critical_threshold", 90)
    cpu_warn = getattr(config, "cpu_warning_threshold", 80)
    mem_warn = getattr(config, "memory_warning_threshold", 80)
    if cpu > cpu_crit or mem > mem_crit:
        return "CRITICAL"
    if cpu > cpu_warn or mem > mem_warn:
        return "WARNING"
    return "OK"


def _collect_system_metrics() -> Dict[str, Any]:
    """Collect basic CPU, memory, and GPU metrics."""
    metrics: Dict[str, Any] = {}
    try:
        from ..resource_monitor import _get_gpu_stats
        from .system_monitor import SystemMonitor

        if _system_monitor:
            metrics.update(_system_monitor.metrics)
        else:
            cpu_percent, memory_percent = SystemMonitor.collect()
            metrics.update(
                {
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory_percent,
                }
            )

        import psutil

        mem = psutil.virtual_memory()
        proc = psutil.Process()
        metrics.setdefault("cpu_percent", psutil.cpu_percent(interval=None))
        metrics.setdefault("memory_percent", getattr(mem, "percent", 0.0))
        mem_used = getattr(mem, "used", 0)
        metrics["memory_used_mb"] = float(mem_used) / (1024 * 1024)
        metrics["process_memory_mb"] = proc.memory_info().rss / (1024 * 1024)
        gpu_percent, gpu_mem = _get_gpu_stats()
        metrics["gpu_percent"] = gpu_percent
        metrics["gpu_memory_mb"] = gpu_mem
    except Exception as e:
        log.warning("Failed to collect system metrics", exc_info=e)

    metrics["queries_total"] = int(orch_metrics.QUERY_COUNTER._value.get())
    metrics["tokens_in_total"] = int(orch_metrics.TOKENS_IN_COUNTER._value.get())
    metrics["tokens_out_total"] = int(orch_metrics.TOKENS_OUT_COUNTER._value.get())
    metrics["health"] = _calculate_health(
        metrics.get("cpu_percent", 0), metrics.get("memory_percent", 0)
    )
    return metrics


def _render_metrics(data: Dict[str, Any]) -> Table:
    table = Table(title="System Metrics")
    table.add_column("Metric")
    table.add_column("Value")
    for k, v in data.items():
        if k == "health":
            color = {
                "OK": "green",
                "WARNING": "yellow",
                "CRITICAL": "red",
            }.get(str(v), "green")
            table.add_row(k, f"[{color}]{v}[/{color}]")
        else:
            table.add_row(str(k), f"{v:.2f}" if isinstance(v, float) else str(v))
    return table


def _collect_graph_data() -> Dict[str, List[str]]:
    """Collect a snapshot of the in-memory knowledge graph."""
    try:
        from ..storage import StorageManager

        G = StorageManager.get_graph()
        data: Dict[str, List[str]] = {}
        for edge in G.edges():
            if len(edge) < 2:
                continue
            u, v = edge[0], edge[1]
            data.setdefault(str(u), []).append(str(v))
        return data
    except Exception:
        return {}


def _render_graph(data: Dict[str, List[str]], *, tree: bool = False) -> Union[Table, Tree]:
    if tree:
        root = Tree("Knowledge Graph")
        for node, edges in data.items():
            branch = root.add(node)
            for edge in edges:
                branch.add(edge)
        return root

    table = Table(title="Knowledge Graph")
    table.add_column("Node")
    table.add_column("Edges")
    for node, edges in data.items():
        table.add_row(node, ", ".join(edges))
    if not data:
        table.add_row("(empty)", "")
    return table


@monitor_app.command("metrics")
def metrics(
    watch: bool = typer.Option(False, "--watch", "-w", help="Refresh continuously")
) -> None:
    """Display system metrics in real time."""
    console = Console()

    def refresh() -> Table:
        return _render_metrics(_collect_system_metrics())

    if watch:
        with Live(refresh(), console=console, refresh_per_second=1) as live:
            try:
                while True:
                    time.sleep(1)
                    live.update(refresh())
            except KeyboardInterrupt:
                pass
    else:
        console.print(refresh())


@monitor_app.command("resources")
def resources(
    duration: int = typer.Option(5, "--duration", "-d", help="Seconds to monitor")
) -> None:
    """Record CPU, memory and GPU usage over time."""
    console = Console()
    tracker = orch_metrics.OrchestrationMetrics()
    end_time = time.time() + duration
    with Progress() as progress:
        task = progress.add_task("[green]Collecting...", total=duration)
        while time.time() < end_time:
            tracker.record_system_resources()
            time.sleep(1)
            progress.update(task, advance=1)

    table = Table(title="Resource Usage")
    table.add_column("Time")
    table.add_column("CPU %")
    table.add_column("Memory MB")
    table.add_column("GPU %")
    table.add_column("GPU MB")
    for rec in tracker.get_summary()["resource_usage"]:
        t = time.strftime("%H:%M:%S", time.localtime(rec["timestamp"]))
        table.add_row(
            t,
            f"{rec['cpu_percent']:.2f}",
            f"{rec['memory_mb']:.2f}",
            f"{rec.get('gpu_percent', 0.0):.2f}",
            f"{rec.get('gpu_memory_mb', 0.0):.2f}",
        )
    console.print(table)


@monitor_app.command("graph")
def graph(
    tree: bool = typer.Option(False, "--tree", help="Show graph as a tree"),
    tui: bool = typer.Option(False, "--tui", help="Display graph in TUI panel"),
) -> None:
    """Display a simple textual view of the knowledge graph."""
    console = Console()
    data = _collect_graph_data()
    if tui:
        from rich.panel import Panel

        console.print(Panel(_render_graph(data, tree=True), title="Graph View"))
    else:
        console.print(_render_graph(data, tree=tree))


@monitor_app.command("run")
def run() -> None:
    """Start the interactive monitor."""
    from ..main import Prompt  # Local import to avoid circular dependency

    console = Console()
    config = _loader.load_config()

    abort_flag = {"stop": False}

    def on_cycle_end(loop: int, state: QueryState) -> None:
        metrics = state.metadata.get("execution_metrics", {})
        table = Table(title=f"Cycle {loop + 1} Metrics")
        table.add_column("Metric")
        table.add_column("Value")
        for k, v in metrics.items():
            table.add_row(str(k), str(v))
        console.print(table)

        console.print(_render_metrics(_collect_system_metrics()))

        # Show token budget usage over time if available
        budget = getattr(config, "token_budget", None)
        usage = metrics.get("total_tokens", {}).get("total", 0)
        if budget is not None:
            usage_table = Table(title="Token Budget")
            usage_table.add_column("Budget")
            usage_table.add_column("Used")
            usage_table.add_row(str(budget), str(usage))
            console.print(usage_table)
        feedback = Prompt.ask("Feedback (q to stop)", default="")
        if feedback.lower() == "q":
            state.error_count = getattr(config, "max_errors", 3)
            abort_flag["stop"] = True
        elif feedback:
            state.claims.append(normalize_reasoning_step({"type": "feedback", "text": feedback}))

    while True:
        query = Prompt.ask("Enter query (q to quit)")
        if not query or query.lower() == "q":
            break

        try:
            loops = getattr(config, "loops", 1)
            with Progress() as progress:
                task = progress.add_task("[green]Processing query...", total=loops)

                def wrapped_on_cycle(loop: int, state: QueryState) -> None:
                    progress.update(task, advance=1)
                    on_cycle_end(loop, state)

                result = Orchestrator().run_query(query, config, {"on_cycle_end": wrapped_on_cycle})
            fmt = config.output_format or ("json" if not sys.stdout.isatty() else "markdown")
            OutputFormatter.format(result, fmt)
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {str(e)}")
        if abort_flag["stop"]:
            break


@monitor_app.command("start")
def start(
    interval: float = typer.Option(None, "--interval", "-i", help="Sampling interval"),
    prometheus: bool = typer.Option(False, "--prometheus", help="Expose Prometheus metrics"),
    port: int = typer.Option(8001, "--port", help="Prometheus server port"),
) -> None:
    """Launch continuous resource monitoring."""
    global _system_monitor
    if interval is None:
        interval = _loader.load_config().monitor_interval
    monitor = ResourceMonitor(interval=interval)
    _system_monitor = SystemMonitor(interval=interval)
    monitor.start(prometheus_port=port if prometheus else None)
    _system_monitor.start()
    typer.echo("Monitoring started. Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        typer.echo("Stopping...")
    finally:
        monitor.stop()
        if _system_monitor:
            _system_monitor.stop()
            _system_monitor = None


from . import cli as _cli  # noqa: E402,F401
