"""Interactive monitoring commands for Autoresearch."""

from __future__ import annotations

import sys
import time
from typing import Any, Dict, List

import typer
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt
from rich.progress import Progress
from rich.live import Live
from .orchestration import metrics as orch_metrics

from .config import ConfigLoader
from .orchestration.orchestrator import Orchestrator
from .orchestration.state import QueryState
from .output_format import OutputFormatter

monitor_app = typer.Typer(help="Monitoring utilities", invoke_without_command=True)

_loader = ConfigLoader()


@monitor_app.callback(invoke_without_command=True)
def default_callback(
    ctx: typer.Context,
    watch: bool = typer.Option(False, "--watch", "-w", help="Refresh continuously"),
) -> None:
    """Display system metrics when no subcommand is provided."""
    if ctx.invoked_subcommand is None:
        metrics(watch=watch)


def _calculate_health(cpu: float, mem: float) -> str:
    if cpu > 90 or mem > 90:
        return "CRITICAL"
    if cpu > 80 or mem > 80:
        return "WARNING"
    return "OK"


def _collect_system_metrics() -> Dict[str, Any]:
    """Collect basic CPU and memory metrics."""
    metrics: Dict[str, Any] = {}
    try:
        import psutil  # type: ignore

        metrics["cpu_percent"] = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory()
        metrics["memory_percent"] = mem.percent
        metrics["memory_used_mb"] = mem.used / (1024 * 1024)
        proc = psutil.Process()
        metrics["process_memory_mb"] = proc.memory_info().rss / (1024 * 1024)
    except Exception:
        pass

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
        from .storage import StorageManager

        G = StorageManager.get_graph()
        data: Dict[str, List[str]] = {}
        for u, v in G.edges():
            data.setdefault(str(u), []).append(str(v))
        return data
    except Exception:
        return {}


def _render_graph(data: Dict[str, List[str]]) -> Table:
    table = Table(title="Knowledge Graph")
    table.add_column("Node")
    table.add_column("Edges")
    for node, edges in data.items():
        table.add_row(node, ", ".join(edges))
    if not data:
        table.add_row("(empty)", "")
    return table


@monitor_app.command("metrics")
def metrics(watch: bool = typer.Option(False, "--watch", "-w", help="Refresh continuously")) -> None:
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
    """Record CPU and memory usage over time."""
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
    for rec in tracker.get_summary()["resource_usage"]:
        t = time.strftime("%H:%M:%S", time.localtime(rec["timestamp"]))
        table.add_row(t, f"{rec['cpu_percent']:.2f}", f"{rec['memory_mb']:.2f}")
    console.print(table)


@monitor_app.command("graph")
def graph() -> None:
    """Display a simple textual view of the knowledge graph."""
    console = Console()
    data = _collect_graph_data()
    console.print(_render_graph(data))


@monitor_app.command("run")
def run() -> None:
    """Start the interactive monitor."""
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
            state.claims.append({"type": "feedback", "text": feedback})

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

                result = Orchestrator.run_query(
                    query, config, {"on_cycle_end": wrapped_on_cycle}
                )
            fmt = config.output_format or (
                "json" if not sys.stdout.isatty() else "markdown"
            )
            OutputFormatter.format(result, fmt)
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {str(e)}")
        if abort_flag["stop"]:
            break
