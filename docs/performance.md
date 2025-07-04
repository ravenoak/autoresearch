# Performance Monitoring

Autoresearch includes tools to inspect system performance and resource usage.

## CPU and Memory Tracking

Use the following command to record CPU and memory statistics:

```bash
autoresearch monitor resources --duration 10
```

This collects metrics for ten seconds and displays them in a table. The duration can be adjusted as needed.

You can also run `autoresearch monitor` to view a live stream of basic metrics.

## Token Usage Heuristics

The orchestration metrics module provides helpers to automatically compress
prompts and adjust token budgets. After each cycle the orchestrator uses
`suggest_token_budget` to expand or shrink the configured budget based on
actual usage. `compress_prompt_if_needed` can shorten prompts when they exceed
a given budget, helping prevent runaway token consumption.

