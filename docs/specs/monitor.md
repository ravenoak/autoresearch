# Monitor

## Overview

Monitoring commands and helpers for Autoresearch. The Typer application exposes
metrics snapshots, resource recordings, knowledge graph inspection, interactive
query loops, background monitors, and a node health server. All commands call
`orch_metrics.ensure_counters_initialized` before execution. Algorithms and
reliability analysis appear in [monitor CLI](../algorithms/monitor_cli.md).

## Algorithms

### metrics

1. Collect system metrics via `_collect_system_metrics`, aggregating CPU,
   memory, GPU, and orchestration counters.
2. Render a Rich table (`_render_metrics`).
3. When `--watch` is provided, refresh the table every second using `Live`
   without mutating counters.

### resources

1. Instantiate `OrchestrationMetrics` to record system resource samples for the
   requested duration.
2. Loop until the timer expires, recording CPU, memory, and GPU values once per
   second and updating a progress bar.
3. Print a summary table when sampling completes.

### graph

1. Read the in-memory knowledge graph via `StorageManager.get_graph()` when
   available.
2. Render a table of edges or a Rich `Tree` when `--tree` or `--tui` is set.

### run

1. Prompt for queries until the user enters `""` or `"q"`.
2. Execute `Orchestrator.run_query` with an `on_cycle_end` callback that prints
   cycle metrics, system metrics, and token budget usage.
3. Collect optional feedback; on `"q"`, set `state.error_count` to force exit
   via the configured `max_errors` threshold.
4. Format the final result using `OutputFormatter` without initialising storage.

### start

1. Determine the sampling interval from CLI options or configuration.
2. Start `ResourceMonitor` (with optional Prometheus export) and
   `SystemMonitor`, storing the latter globally for reuse by `metrics`.
3. Loop until interrupted, then stop both monitors and clear global state.

### serve

1. Instantiate `NodeHealthMonitor` with optional Redis URL, Ray address, port,
   and interval.
2. Start the Prometheus HTTP server and background check thread.
3. Sleep until interrupted, then stop the monitor and exit with status 0.

## Invariants

- `metrics` reads orchestration counters but never increments them.
- `_system_monitor` is started only once and stopped when `start` exits, keeping
  metrics consistent for subsequent commands.
- `NodeHealthMonitor` gauges reset to zero before each health check, ensuring
  stale values do not persist.
- `run` does not initialise storage directly; it relies on orchestrator
  callbacks so monitors can operate without database configuration.
- `serve` always stops the monitor thread before exiting, preventing orphaned
  background work.

## Proof Sketch

`monitor` commands are thin wrappers around the primitives documented in
[monitor CLI](../algorithms/monitor_cli.md). Each command prints deterministic
Rich output and guards cleanup paths with `try`/`finally` blocks so monitors
stop reliably. Unit tests exercise CLI entry points, metrics collection,
feedback loops, and GPU/resource integration, providing empirical evidence
that the invariants hold.

## Simulation Expectations

[monitor_cli_reliability.py][s1] runs Monte Carlo analyses of sampling latency
and failure rates, while GPU/resource tests simulate environments with and
without GPU metrics to confirm graceful degradation.

## Traceability

- Modules
  - [src/autoresearch/monitor/__init__.py][m1]
  - [src/autoresearch/monitor/cli.py][m2]
  - [src/autoresearch/monitor/metrics.py][m3]
  - [src/autoresearch/monitor/node_health.py][m4]
  - [src/autoresearch/monitor/system_monitor.py][m5]
- Tests
  - [tests/unit/test_main_monitor_commands.py][t1]
  - [tests/unit/test_monitor_cli.py][t2]
  - [tests/unit/test_resource_monitor_gpu.py][t3]
  - [tests/integration/test_monitor_metrics.py][t4]

[m1]: ../../src/autoresearch/monitor/__init__.py
[m2]: ../../src/autoresearch/monitor/cli.py
[m3]: ../../src/autoresearch/monitor/metrics.py
[m4]: ../../src/autoresearch/monitor/node_health.py
[m5]: ../../src/autoresearch/monitor/system_monitor.py
[t1]: ../../tests/unit/test_main_monitor_commands.py
[t2]: ../../tests/unit/test_monitor_cli.py
[t3]: ../../tests/unit/test_resource_monitor_gpu.py
[t4]: ../../tests/integration/test_monitor_metrics.py
[s1]: ../../scripts/monitor_cli_reliability.py
