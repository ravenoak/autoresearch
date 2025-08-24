# Monitor

Interactive monitoring commands for Autoresearch. See
[monitor CLI algorithm](../algorithms/monitor_cli.md) for command flow and
error handling.

The metrics command reports system statistics without changing the
`autoresearch_queries_total` counter. Monitor commands now skip storage
initialization so metrics can be displayed without a configured database.

## Traceability

- Modules
  - [src/autoresearch/monitor/][m1]
- Tests
  - [tests/unit/test_main_monitor_commands.py][t1]
  - [tests/unit/test_monitor_cli.py][t2]
  - [tests/unit/test_resource_monitor_gpu.py][t3]

[m1]: ../../src/autoresearch/monitor/
[t1]: ../../tests/unit/test_main_monitor_commands.py
[t2]: ../../tests/unit/test_monitor_cli.py
[t3]: ../../tests/unit/test_resource_monitor_gpu.py
