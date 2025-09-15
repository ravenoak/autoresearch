# Monitor CLI

The `autoresearch monitor` subcommands surface runtime metrics, resource
sampling, knowledge graph inspection, interactive orchestration, and health
checks.

## Flow

1. `monitor metrics` prints a single snapshot of CPU, memory, GPU, and token
   counters collected by `_collect_system_metrics`.
2. `monitor metrics --watch` refreshes the snapshot every second using Rich
   `Live` updates without mutating counters.
3. `monitor resources` records samples for a configurable duration and renders a
   summary table of the collected points.
4. `monitor graph` queries the in-memory knowledge graph and prints either a
   table of edges or a Rich tree when `--tree`/`--tui` are supplied.
5. `monitor run` prompts for queries, runs the orchestrator with live cycle
   metrics, gathers optional feedback, and exits when the user types `q`.
6. `monitor start` launches `ResourceMonitor` and `SystemMonitor`, optionally
   exposing Prometheus metrics, and runs until interrupted.
7. `monitor serve` starts `NodeHealthMonitor`, exposes Prometheus gauges for
   Redis and Ray checks, and stops cleanly on Ctrl+C.

## Interrupt Handling

- `monitor start` and `monitor serve` wrap long-running loops in `try`/`finally`
  blocks so monitors stop and global state resets when interrupted.

## Error Handling

- Failures while collecting metrics log warnings but still produce best-effort
  output, allowing commands to complete without raising exceptions.
- Health check failures set gauges to zero, keeping Prometheus output consistent
  even when dependencies are unreachable.

## Reliability Analysis

A Monte Carlo model estimates how often metrics collection fails and the latency
of successful samples:

```bash
uv run scripts/monitor_cli_reliability.py --runs 1000 --fail-rate 0.05
```

The simulation informs retry budgets and sampling intervals.

## References

- [src/autoresearch/monitor/](../../src/autoresearch/monitor/)
- [scripts/monitor_cli_reliability.py](../../scripts/monitor_cli_reliability.py)
- [tests/unit/test_monitor_cli.py](../../tests/unit/test_monitor_cli.py)
- [tests/unit/test_main_monitor_commands.py](../../tests/unit/
  test_main_monitor_commands.py)
- [tests/integration/test_monitor_metrics.py](../../tests/integration/
  test_monitor_metrics.py)
- [tests/unit/test_resource_monitor_gpu.py](../../tests/unit/
  test_resource_monitor_gpu.py)
