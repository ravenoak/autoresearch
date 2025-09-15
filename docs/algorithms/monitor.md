# Monitor

## Overview
The monitor package collects runtime metrics and exposes a CLI.

## Algorithm
`monitor metrics` initializes counters, gathers CPU, memory, and GPU data,
and prints a table without mutating ``autoresearch_queries_total``.
`monitor run` prompts for queries, executes them for a number of cycles,
and displays metrics after each cycle while skipping storage
initialization. Both commands rely on a background loop that polls system
resources and pushes samples to a shared queue.

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
