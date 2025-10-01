"""Analytical model of distributed orchestrator scheduling."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class SimulationResult:
    """Structured metrics describing an orchestrator simulation run."""

    avg_latency_s: float
    throughput: float
    cpu_percent: float
    memory_mb: float


def _validate_arguments(workers: int, tasks: int, network_latency: float, task_time: float) -> None:
    """Validate simulation parameters raising ``SystemExit`` on failure."""

    if workers <= 0:
        raise SystemExit("workers must be > 0")
    if tasks <= 0:
        raise SystemExit("tasks must be > 0")
    if network_latency < 0:
        raise SystemExit("network_latency must be >= 0")
    if task_time <= 0:
        raise SystemExit("task_time must be > 0")


def _compute_utilization(workers: int, network_latency: float, task_time: float) -> float:
    """Approximate worker utilization for the analytical model."""

    dispatch_interval = network_latency + task_time
    if dispatch_interval == 0:
        return 0.0
    utilization = task_time / (dispatch_interval * workers)
    return min(0.95, utilization)


def _compute_latency(network_latency: float, task_time: float, utilization: float) -> float:
    """Estimate average latency including queueing penalty."""

    return network_latency + task_time * (1.0 + utilization)


def _compute_throughput(
    tasks: int,
    workers: int,
    network_latency: float,
    task_time: float,
    utilization: float,
) -> float:
    """Estimate throughput by scaling the dispatch cadence with queueing overhead."""

    dispatch_interval = network_latency + task_time
    base_duration = tasks * dispatch_interval / workers
    wait_penalty = 1.0 + 2.0 * utilization
    duration = base_duration * wait_penalty
    if duration <= 0:
        return float("inf")
    return tasks / duration


def _compute_cpu_percent(workers: int, utilization: float) -> float:
    """Approximate CPU usage as utilization scales with worker count."""

    return min(100.0, 10.0 + utilization * 90.0 * min(workers, 4) / 4)


def _compute_memory(workers: int) -> float:
    """Approximate memory consumption for bookkeeping state."""

    return 48.0 + workers * 1.5


def run_simulation(
    workers: int,
    tasks: int,
    network_latency: float = 0.005,
    task_time: float = 0.005,
) -> dict[str, float]:
    """Process tasks analytically and return summary metrics as a dictionary."""

    _validate_arguments(workers, tasks, network_latency, task_time)

    utilization = _compute_utilization(workers, network_latency, task_time)
    latency = _compute_latency(network_latency, task_time, utilization)
    throughput = _compute_throughput(tasks, workers, network_latency, task_time, utilization)
    cpu_percent = _compute_cpu_percent(workers, utilization)
    memory_mb = _compute_memory(workers)
    result = SimulationResult(
        avg_latency_s=latency,
        throughput=throughput,
        cpu_percent=cpu_percent,
        memory_mb=memory_mb,
    )
    return asdict(result)


def main(workers: int, tasks: int, network_latency: float, task_time: float) -> dict[str, float]:
    """Run the simulation and print summary metrics."""

    metrics = run_simulation(
        workers=workers, tasks=tasks, network_latency=network_latency, task_time=task_time
    )
    print(json.dumps(metrics))
    return metrics


if __name__ == "__main__":  # pragma: no cover
    parser = argparse.ArgumentParser(
        description="Distributed orchestrator scheduling simulation"
    )
    parser.add_argument("--workers", type=int, default=2, help="number of worker processes")
    parser.add_argument("--tasks", type=int, default=100, help="tasks to schedule")
    parser.add_argument(
        "--network-latency",
        type=float,
        default=0.005,
        help="simulated dispatch latency per task (s)",
    )
    parser.add_argument(
        "--task-time",
        type=float,
        default=0.005,
        help="simulated compute time per task (s)",
    )
    args = parser.parse_args()
    main(args.workers, args.tasks, args.network_latency, args.task_time)
