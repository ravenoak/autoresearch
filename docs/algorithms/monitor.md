# Monitor

## Overview

The monitor package hosts the Typer application registered as
`autoresearch monitor`. Its commands display live system metrics, stream
resource usage, inspect the knowledge graph, run an interactive orchestrator,
and supervise background monitors. CLI output is aligned with the Prometheus
gauges exposed by `ResourceMonitor`, `SystemMonitor`, and `NodeHealthMonitor`.

## Components

### CLI commands

- `monitor metrics` prints CPU, memory, GPU, and counter totals, optionally
  refreshing once per second with `--watch`.
- `monitor resources` records one sample per second and renders a table of CPU
  percent, memory MB, GPU percent, and GPU memory MB.
- `monitor graph` shows the knowledge graph as a table, tree, or TUI panel
  depending on the options supplied.
- `monitor run` prompts for queries, drives `Orchestrator.run_query()` with a
  progress bar, prints cycle metrics plus current system metrics, and collects
  optional feedback.
- `monitor start` launches `ResourceMonitor` and `SystemMonitor`, optionally
  exposing Prometheus gauges on the configured port, and stops both monitors on
  interrupt.
- `monitor serve` wraps `NodeHealthMonitor` to publish Redis and Ray health
  gauges before exiting cleanly on Ctrl+C.

### Background monitors

- `SystemMonitor` records CPU and memory percentages in a daemon thread and
  stores the latest snapshot for CLI reuse.
- `ResourceMonitor` logs process and GPU usage, snapshots token counters, and
  serves Prometheus gauges when requested.
- `NodeHealthMonitor` probes Redis and Ray, updating gauges that report service
  availability and overall node health.

## Algorithm

1. A Typer callback invokes `orch_metrics.ensure_counters_initialized()` before
   any command executes.
2. `_collect_system_metrics` merges `_system_monitor.metrics` when a background
   sampler is active; otherwise it calls `SystemMonitor.collect()` and augments
   the snapshot with psutil and GPU data.
3. All counter totals are read via `_value.get()` to avoid mutating metrics.
4. `monitor run` drives `Orchestrator.run_query()` with an `on_cycle_end`
   callback that prints execution metrics, renders system metrics, and applies
   the configured token budget.
5. `monitor start` and `monitor serve` wrap long-running loops in
   `try`/`finally` so both monitors stop and module state resets after
   interrupts.
6. `metrics_endpoint` returns `generate_latest()` and `CONTENT_TYPE_LATEST` so
   Prometheus scrapers and the CLI share the same data.

## Proof sketch

- `tests/unit/test_monitor_metrics_init.py` confirms the Typer callback
  initialises counters.
- `tests/unit/test_monitor_cli.py` checks metric output, ensures counters do not
  change during snapshots, and verifies interactive flow handling.
- `tests/unit/test_main_monitor_commands.py` validates CLI wiring plus clean
  shutdown for `monitor start` and `monitor serve`.
- `tests/unit/test_system_monitor.py` verifies background sampling updates CPU
  and memory gauges.
- `tests/unit/test_node_health_monitor_property.py` covers gauge updates for
  Redis and Ray availability.
- `tests/integration/test_monitor_metrics.py` exercises Prometheus exposure,
  resource sampling tables, and query counter increments.

## Simulation

`scripts/monitor_cli_reliability.py` simulates metrics collection latency and
failure rates. Running

```
uv run scripts/monitor_cli_reliability.py --runs 1000 --fail-rate 0.05
```

provides `average_latency_ms` and `success_rate` estimates that inform retry
budgets. Integration tests also cover GPU-present and GPU-absent scenarios so
resource sampling remains robust.

## References

- [spec](../specs/monitor.md)
- [code](../../src/autoresearch/monitor/)
- [tests](../../tests/unit/test_monitor_cli.py)
- [tests/integration/test_monitor_metrics.py](../../tests/integration/
  test_monitor_metrics.py)

## Related Issues

- [Fix monitor CLI metrics failure][issue]

[issue]: ../../issues/archive/fix-monitor-cli-metrics-failure.md
