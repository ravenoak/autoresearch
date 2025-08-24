# Monitor

Interactive monitoring commands for Autoresearch.

The metrics command increments the `autoresearch_queries_total` counter each
time system statistics are collected. Monitor commands now skip storage
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
