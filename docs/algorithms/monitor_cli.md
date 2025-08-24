# Monitor CLI

The `autoresearch monitor` commands stream system metrics and resource usage.

## Flow

1. `monitor` prints a single snapshot of CPU, memory, and token counts.
2. `monitor -w` refreshes the snapshot every second.
3. `monitor resources` collects samples for a duration and reports
   aggregates.
4. `monitor start --prometheus` launches a Prometheus metrics endpoint.

## Error Handling

- If metrics collection fails, a friendly message is printed and exit code 1
  is returned.
- When the endpoint fails to start, the command stops gracefully without
  leaving background threads.

## References

- [src/autoresearch/monitor/](../../src/autoresearch/monitor/)
- [tests/unit/test_monitor_cli.py](../../tests/unit/test_monitor_cli.py)
