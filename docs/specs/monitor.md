# Monitor

## Overview

The monitor package binds a Typer application under `autoresearch monitor`
to surface orchestration metrics, explore the knowledge graph, and manage
background health samplers. CLI commands share the `ResourceMonitor` and
`SystemMonitor` samplers with the HTTP server so terminal snapshots and
Prometheus scrapers observe the same gauges. The package also exposes an
async `metrics_endpoint` for FastAPI routers and a `monitor serve` command
that wraps `NodeHealthMonitor` for Redis and Ray health reporting.

## Algorithms

### metrics

1. `_collect_system_metrics` reuses `_system_monitor.metrics` when a background
   sampler is running; otherwise it calls `SystemMonitor.collect()` for a fresh
   snapshot.
2. psutil adds CPU percent, virtual memory percent, total memory usage in MB,
   and process RSS in MB. GPU utilisation and memory in MB come from
   `resource_monitor._get_gpu_stats()`, and missing values default to zero.
3. Counter totals come from `orch_metrics.*._value.get()`, and
   `_calculate_health` classifies CPU and memory load using warning and
   critical thresholds from `ConfigLoader`.
4. `_render_metrics` prints a Rich table; with `--watch` the command refreshes
   the table once per second via `Live`, otherwise it emits a single snapshot.

### resources

1. Instantiate `OrchestrationMetrics` and compute the end time from the
   requested `--duration`.
2. Sleep in one second increments, calling `record_system_resources()` each
   loop while advancing a Rich progress bar.
3. Render a table that includes timestamps plus CPU percent, memory MB, GPU
   percent, and GPU memory MB for every recorded sample.

### graph

1. `_collect_graph_data` attempts `StorageManager.get_graph()` to build a map of
   node IDs to outgoing edges, falling back to `{}` when storage is not
   configured.
2. With `--tui` the command wraps a `Tree` in a `Panel`; otherwise `--tree`
   prints a `Tree` and the default formatting renders a table.

### run

1. Load the active configuration, prompt for queries, and exit when the user
   enters an empty string or `q`.
2. For each query create a progress bar sized to `config.loops` and call
   `Orchestrator.run_query()` with an `on_cycle_end` callback that advances the
   bar.
3. The callback prints a table of `execution_metrics`, appends the current
   system metrics table, and, when `token_budget` is configured, shows a
   `Budget` versus `Used` table.
4. Feedback collected via `Prompt.ask` attaches structured claims. Entering `q`
   sets `state.error_count` to `config.max_errors` (default 3) and toggles an
   abort flag so the outer loop terminates after the current run.
5. Results flow through `OutputFormatter.format()` using `config.output_format`
   or `json` when stdout is not a TTY. Exceptions are reported without aborting
   the CLI.

### start

1. Derive the sampling interval from `--interval` or `config.monitor_interval`.
2. Instantiate `ResourceMonitor` and set the module level `_system_monitor` to a
   matching `SystemMonitor`.
3. Start both monitors, exposing Prometheus metrics on the requested port when
   `--prometheus` is provided, and print a status banner.
4. Sleep until interrupted, then stop both monitors inside `finally` and clear
   `_system_monitor` so future calls return fresh snapshots.

### serve

1. Build `NodeHealthMonitor` with the provided Redis URL, Ray address, port, and
   interval.
2. Print startup messages, invoke `monitor.start()` (launching the HTTP server
   and background thread), and sleep until interrupted.
3. On `KeyboardInterrupt` or `SystemExit`, log shutdown, call `monitor.stop()`
   inside `finally`, and exit with `typer.Exit(0)`.

### metrics_endpoint

1. `metrics_endpoint` returns a `PlainTextResponse` containing
   `generate_latest()` output and `CONTENT_TYPE_LATEST`, so HTTP clients receive
   Prometheus-formatted metrics with a `200` status code.

### system_monitor

1. `_gauge` obtains gauges from a Prometheus registry, resetting reused gauges
   to zero to avoid stale samples.
2. `SystemMonitor.start()` spawns a daemon thread that repeatedly calls
   `collect()`, updates `self.metrics`, and synchronises CPU and memory gauges.
3. `collect()` delegates to psutil to read CPU and memory percentages without
   blocking.
4. `stop()` signals the thread to halt and joins it, leaving `self.metrics`
   populated with the latest snapshot.

### node_health

1. `NodeHealthMonitor` registers gauges for Redis, Ray, and overall node health,
   zeroing reused gauges through `_gauge`.
2. `start()` optionally launches a Prometheus server, spawns a daemon thread,
   and repeatedly calls `check_once()` until stopped.
3. `check_once()` runs Redis and Ray probes, writing `1` for healthy endpoints
   and `0` otherwise while updating the composite health gauge.
4. `stop()` joins the thread and leaves gauges in their latest state.

## Invariants

- The Typer callback always initialises orchestration counters before any
  command executes.
- `_collect_system_metrics` reuses cached snapshots when available and only
  reads orchestration counters, so CLI commands never mutate totals.
- Health classifications use configuration thresholds with safe defaults when
  values are missing.
- `_system_monitor` is created once per `start` invocation and cleared in the
  `finally` block, keeping subsequent `metrics` commands consistent.
- `_gauge` zeroes Prometheus gauges before reuse and both monitors overwrite
  gauge values each interval, preventing stale readings.
- `ResourceMonitor.start()` and `SystemMonitor.start()` guard against duplicate
  threads, making repeated `start` invocations idempotent.
- `serve` always executes `monitor.stop()` through its `finally` block, so the
  background health thread halts even after interrupts.

## Proof Sketch

- `tests/unit/test_monitor_metrics_init.py` confirms the Typer callback
  initialises counters before commands run.
- `tests/unit/test_monitor_cli.py` verifies the `metrics` command prints CPU,
  memory, GPU, and counter data, and that `run` routes callbacks and honours
  feedback.
- `tests/unit/test_main_monitor_commands.py` exercises the CLI wiring and
  ensures `monitor start` and `monitor serve` shut down their monitors on exit.
- `tests/unit/test_system_monitor.py` confirms `SystemMonitor` captures CPU and
  memory percentages and exposes them through gauges.
- `tests/unit/test_node_health_monitor_property.py` shows gauge updates match
  Redis and Ray health outcomes.
- `tests/integration/test_monitor_metrics.py` covers Prometheus scraping,
  resource sampling tables, and counter increments across the CLI and HTTP
  surfaces.

## Simulation Evidence

`scripts/monitor_cli_reliability.py` performs a Monte Carlo simulation of
metrics collection latency and failure probability. Run

```
uv run scripts/monitor_cli_reliability.py --runs 1000 --fail-rate 0.05
```

to obtain `average_latency_ms` and `success_rate` estimates. Integration tests
also exercise GPU present and absent scenarios so resource sampling and counter
snapshots degrade gracefully when GPU metrics are unavailable.

## Traceability

- Modules
  - [src/autoresearch/monitor/__init__.py][m1]
  - [src/autoresearch/monitor/cli.py][m2]
  - [src/autoresearch/monitor/metrics.py][m3]
  - [src/autoresearch/monitor/node_health.py][m4]
  - [src/autoresearch/monitor/system_monitor.py][m5]
  - [src/autoresearch/resource_monitor.py][m6]
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
[m6]: ../../src/autoresearch/resource_monitor.py
[s1]: ../../scripts/monitor_cli_reliability.py
[t1]: ../../tests/unit/test_main_monitor_commands.py
[t2]: ../../tests/unit/test_monitor_cli.py
[t3]: ../../tests/unit/test_monitor_metrics_init.py
[t4]: ../../tests/unit/test_node_health_monitor_property.py
[t5]: ../../tests/unit/test_system_monitor.py
[t6]: ../../tests/integration/test_monitor_metrics.py
