# Monitor

## Overview

Interactive monitoring commands for Autoresearch. See
[monitor CLI algorithm](../algorithms/monitor_cli.md) for command flow and
error handling. The metrics command reports system statistics without changing
the `autoresearch_queries_total` counter. Monitor commands skip storage
initialization so metrics can run without a configured database.

## Algorithms

### Command Flow

#### metrics

1. Initialize orchestration counters.
2. Collect CPU, memory, and GPU data with ``_collect_system_metrics``.
3. Render a table to the console.
   - Invariant: ``queries_total_after = queries_total_before``.

#### run

1. Prompt for queries until ``""`` or ``"q"`` is entered.
2. For each query:
   - Execute ``Orchestrator.run_query`` for ``loops`` cycles.
   - After each cycle, display system metrics and cycle metrics.
   - Abort if feedback ``"q"`` forces ``error_count`` to ``max_errors``.
   - Invariant: storage layers remain uninitialized.

## Invariants

- ``monitor metrics`` never mutates ``autoresearch_queries_total``.
- Monitor commands do not initialize ``StorageManager`` before use.

## Complexity

- ``metrics``: time ``Θ(1)``, space ``Θ(1)``.
- ``run``: time ``Θ(loops × C_orchestrator)`` per query, space ``Θ(1)``.

## Proof Sketch

Correctness follows from command flow constraints and invariant checks.

## Simulation Expectations

Monte Carlo analysis lives in
[`monitor_cli_reliability.py`](../../scripts/monitor_cli_reliability.py), which
estimates latency and failure rate. Unit tests cover nominal and edge cases for
these routines.

## Traceability

- Modules
  - [src/autoresearch/monitor/](../../src/autoresearch/monitor/)
- Scripts
  - [scripts/monitor_cli_reliability.py](../../scripts/monitor_cli_reliability.py)
- Tests
  - [tests/unit/test_main_monitor_commands.py](../../tests/unit/test_main_monitor_commands.py)
  - [tests/unit/test_monitor_cli.py](../../tests/unit/test_monitor_cli.py)
  - [tests/unit/test_resource_monitor_gpu.py](../../tests/unit/test_resource_monitor_gpu.py)

