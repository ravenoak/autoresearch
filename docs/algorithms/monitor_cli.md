# Monitor CLI

The `autoresearch monitor` commands stream system metrics and resource usage.

## Flow

1. `monitor` prints a single snapshot of CPU, memory, and token counts.
2. `monitor -w` refreshes the snapshot every second.
3. `monitor resources` collects samples for a duration and reports
   aggregates.
4. `monitor start --prometheus` launches a Prometheus metrics endpoint.
5. `monitor serve` runs a node health server and exits 0 when stopped.

## Interrupt Handling

- `monitor serve` catches `KeyboardInterrupt` and shuts down cleanly.

## Error Handling

- If metrics collection fails, a friendly message is printed and exit code 1
  is returned.
- When the endpoint fails to start, the command stops gracefully without
  leaving background threads.

## Reliability analysis

A Monte Carlo model estimates how often metrics collection fails and the
latency of successful samples. Run the simulation to explore different
failure rates and observe average latency:

```bash
uv run scripts/monitor_cli_reliability.py --runs 1000 --fail-rate 0.05
```

This informs retry budgets and helps tune sampling intervals.

## References

- [src/autoresearch/monitor/](../../src/autoresearch/monitor/)
- [scripts/monitor_cli_reliability.py](../../scripts/monitor_cli_reliability.py)
- [tests/unit/test_monitor_cli.py](../../tests/unit/test_monitor_cli.py)
- [tests/integration/test_monitor_metrics.py](../../tests/integration/test_monitor_metrics.py)
- [tests/behavior/steps/monitor_cli_steps.py](../../tests/behavior/steps/monitor_cli_steps.py)
