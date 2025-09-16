# Monitor

## Overview

The monitor package hosts the Typer application registered as
`autoresearch monitor`. Its commands stream live system metrics, sample
resource usage, inspect the knowledge graph, run an interactive
orchestrator loop, and supervise background monitors. The package also
exposes the async `metrics_endpoint` for FastAPI routers so HTTP clients
can scrape Prometheus metrics alongside the CLI utilities.

A Typer callback calls `orch_metrics.ensure_counters_initialized()`
before every command. `ConfigLoader` supplies CPU and memory thresholds
that drive the health indicator and provides the default sampling
interval when `--interval` is omitted. Background sampling reuses
`ResourceMonitor` and `SystemMonitor`, letting CLI commands and HTTP
scrapers observe the same gauges.

## Algorithms

### metrics

1. `_collect_system_metrics` merges values from `_system_monitor` when a
   background sampler is running; otherwise it calls
   `SystemMonitor.collect()` for a fresh psutil snapshot.
2. psutil adds process RSS and total memory usage, GPU utilisation comes
   from `resource_monitor._get_gpu_stats()`, and orchestration counters
   are read via `._value.get()` without incrementing them.
3. `_calculate_health` compares CPU and memory readings against
   configuration thresholds to add a `health` field, and
   `_render_metrics` colour-codes the row in a Rich table.
4. With `--watch`, `Live` refreshes the table every second until
   interrupted; otherwise the console prints a single snapshot.

### resources

1. Instantiate `OrchestrationMetrics` and compute the end time from the
   requested `--duration`.
2. Loop once per second, calling `record_system_resources()` and
   advancing a Rich progress bar until the timer expires.
3. Query `tracker.get_summary()["resource_usage"]` and render a table
   with timestamps plus CPU, memory, GPU, and GPU-memory columns.

### graph

1. `_collect_graph_data` tries `StorageManager.get_graph()` and builds a
   dictionary of node -> edges, falling back to `{}` when storage is not
   configured.
2. When `--tui` is provided the command wraps a `Tree` view in a Rich
   `Panel`; otherwise it renders a `Tree` when `--tree` is set or a table
   by default.

### run

1. Load the active configuration and prompt for queries until the user
   submits an empty string or `q`.
2. For each query create a progress bar sized to `config.loops` and call
   `Orchestrator.run_query` with an `on_cycle_end` callback that advances
   progress and captures each `QueryState`.
3. The callback prints a table of `execution_metrics`, appends the
   current system metrics table, and, when `token_budget` is configured,
   shows a `Budget` versus `Used` table.
4. Feedback collected with `Prompt.ask` appends structured claims; the
   input `q` sets `state.error_count` to `config.max_errors` (default 3)
   and flips an `abort_flag` so the outer loop terminates after the
   current run.
5. Results are formatted via `OutputFormatter.format` using
   `config.output_format` or falling back to JSON when stdout is not a
   TTY; exceptions are reported without stopping the monitor entirely.

### start

1. Derive the sampling interval from `--interval` or
   `config.monitor_interval`.
2. Instantiate `ResourceMonitor` and assign a new `_system_monitor`
   pointing to `SystemMonitor(interval=interval)`.
3. Start `ResourceMonitor`, passing `prometheus_port=port` when
   `--prometheus` is supplied, and call `_system_monitor.start()`.
4. Print a status banner, sleep until interrupted, then stop both
   monitors inside a `finally` block and clear `_system_monitor`.

### serve

1. Build `NodeHealthMonitor` with the provided Redis URL, Ray address,
   port, and interval.
2. Print startup messages, invoke `monitor.start()` (which launches the
   HTTP server and background thread), and sleep in a loop.
3. On `KeyboardInterrupt` or `SystemExit`, log shutdown, invoke
   `monitor.stop()` inside `finally`, and exit with `typer.Exit(0)`.

### metrics_endpoint

1. `metrics_endpoint` returns a `PlainTextResponse` containing
   `generate_latest()` output and `CONTENT_TYPE_LATEST`, giving HTTP
   clients Prometheus-formatted metrics with status code 200.

## Invariants

- The Typer callback always initialises orchestration counters before any
  command executes.
- `_collect_system_metrics` reuses cached snapshots when possible and
  only reads orchestration counters, so CLI commands never mutate totals.
- `_system_monitor` is created once per `start` invocation and cleared in
  the `finally` block, keeping future `metrics` calls consistent.
- `_gauge` zeroes reused Prometheus gauges and `NodeHealthMonitor.check_once`
  overwrites every gauge each interval, preventing stale readings.
- `ResourceMonitor.start()` and `SystemMonitor.start()` guard against
  duplicate threads, making repeated `start` invocations idempotent.
- `serve` always executes `monitor.stop()` through its `finally` block,
  so the background health thread halts even after interrupts.

## Proof Sketch

- `tests/unit/test_monitor_metrics_init.py` confirms the Typer callback
  initialises counters before commands run.
- `tests/unit/test_monitor_cli.py` verifies the `metrics` command prints
  CPU, memory, GPU, and counter data while `run` routes callbacks and
  honours feedback.
- `tests/unit/test_main_monitor_commands.py` exercises the CLI wiring and
  ensures `monitor serve` stops its monitor on exit.
- `tests/unit/test_node_health_monitor_property.py` uses property tests
  to show gauge updates match Redis/Ray health outcomes.
- `tests/unit/test_system_monitor.py` confirms `SystemMonitor` captures
  CPU and memory percentages and exposes them through gauges.
- `tests/integration/test_monitor_metrics.py` covers Prometheus scraping,
  resource sampling tables, and counter increments across the CLI and
  HTTP surfaces.

## Simulation Evidence

`scripts/monitor_cli_reliability.py` performs a Monte Carlo simulation of
metrics collection latency and failure probability. Run
`uv run scripts/monitor_cli_reliability.py --runs 1000 --fail-rate 0.05`
to obtain `average_latency_ms` and `success_rate` estimates. Integration
tests also simulate GPU present/absent scenarios so resource sampling and
counter snapshots degrade gracefully when GPU metrics are unavailable.

## Traceability

- Modules
  - [src/autoresearch/monitor/__init__.py][m1]
  - [src/autoresearch/monitor/cli.py][m2]
  - [src/autoresearch/monitor/metrics.py][m3]
  - [src/autoresearch/monitor/node_health.py][m4]
  - [src/autoresearch/monitor/system_monitor.py][m5]
- Scripts
  - [scripts/monitor_cli_reliability.py][s1]
- Tests
  - [tests/unit/test_main_monitor_commands.py][t1]
  - [tests/unit/test_monitor_cli.py][t2]
  - [tests/unit/test_monitor_metrics_init.py][t3]
  - [tests/unit/test_node_health_monitor_property.py][t4]
  - [tests/unit/test_system_monitor.py][t5]
  - [tests/integration/test_monitor_metrics.py][t6]

[m1]: ../../src/autoresearch/monitor/__init__.py
[m2]: ../../src/autoresearch/monitor/cli.py
[m3]: ../../src/autoresearch/monitor/metrics.py
[m4]: ../../src/autoresearch/monitor/node_health.py
[m5]: ../../src/autoresearch/monitor/system_monitor.py
[s1]: ../../scripts/monitor_cli_reliability.py
[t1]: ../../tests/unit/test_main_monitor_commands.py
[t2]: ../../tests/unit/test_monitor_cli.py
[t3]: ../../tests/unit/test_monitor_metrics_init.py
[t4]: ../../tests/unit/test_node_health_monitor_property.py
[t5]: ../../tests/unit/test_system_monitor.py
[t6]: ../../tests/integration/test_monitor_metrics.py
