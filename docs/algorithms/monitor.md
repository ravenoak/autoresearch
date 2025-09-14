# Monitor

## Overview
The monitor package collects runtime metrics and exposes a CLI.

## Algorithm
A background loop polls resource usage and writes metrics to a shared
queue for reporting.

## Proof sketch
The loop sleeps between samples and drains the queue each cycle, so
memory use remains bounded.

## Simulation
`tests/unit/test_monitor_cli.py` invokes the CLI and verifies metric
outputs.

## References
- [code](../../src/autoresearch/monitor/)
- [spec](../specs/monitor.md)
- [tests](../../tests/unit/test_monitor_cli.py)

## Related Issues
- [Fix monitor CLI metrics failure][issue]

[issue]: ../../issues/archive/fix-monitor-cli-metrics-failure.md
