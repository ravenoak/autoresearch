# Monitor CLI

The `autoresearch monitor` subcommands expose runtime metrics, streaming
resource samples, knowledge graph inspection, interactive orchestration, and
health checks.

## Flow

1. `monitor metrics` collects CPU percent, memory percent, memory MB, process
   RSS, and GPU metrics via `_collect_system_metrics`, then prints a Rich table
   or refreshes via `Live` when `--watch`.
2. When `_system_monitor` is active, the command merges its cached `metrics`
   into the snapshot so background samplers and CLI output stay consistent.
3. `monitor resources` records one sample per second via
   `OrchestrationMetrics.record_system_resources()` and prints CPU percent,
   memory MB, GPU percent, and GPU memory MB with timestamps.
4. `monitor graph` loads the in-memory knowledge graph and renders either a
   table or Rich tree/Panel depending on `--tree` or `--tui`.
5. `monitor run` prompts for queries, runs each through `Orchestrator.run_query`
   while updating progress, prints execution metrics and live system metrics,
   and collects optional feedback before continuing.
6. `monitor start` launches `ResourceMonitor` and `SystemMonitor`, optionally
   exposing Prometheus gauges on the requested port, and stops both monitors on
   Ctrl+C.
7. `monitor serve` wraps `NodeHealthMonitor`, publishing Redis and Ray health
   gauges and exiting cleanly when interrupted.

## Error Handling

- Metric collection failures log warnings and reuse the last known values so the
  CLI still prints a table.
- Redis or Ray probe failures set the corresponding gauges to zero, keeping
  Prometheus output consistent even when dependencies are unreachable.

## Reliability Analysis

A Monte Carlo model estimates latency and failure rates for the metrics flow:

```
uv run scripts/monitor_cli_reliability.py --runs 1000 --fail-rate 0.05
```

The simulation informs retry budgets and sampling intervals. Integration tests
exercise GPU-present and GPU-absent scenarios to ensure graceful degradation.

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
- [tests/unit/test_system_monitor.py](../../tests/unit/test_system_monitor.py)
