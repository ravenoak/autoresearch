# Performance Tuning

The benchmark script `scripts/benchmark_token_memory.py` measures the token
usage, memory impact, and elapsed time of a minimal query. The current baseline
records a duration of 0.0048 seconds, no measurable memory growth, and 2 input
and 7 output tokens for the Dummy agent.

To keep regressions in check:

- Profile representative queries with `uv run scripts/benchmark_token_memory.py`.
- Investigate runs exceeding 10% of baseline time or memory.
- Reduce token budgets or simplify agents if usage grows beyond the baseline.
- Cache external resources to avoid unpredictable memory spikes.

These measurements are enforced in `tests/benchmark/test_token_memory.py`. Update
the baseline file when deliberate tuning changes expected resource usage.

## Micro-benchmarks

Targeted profiling highlighted hotspots in orchestrator, search, and storage.
Small optimizations yielded incremental gains:

- `Orchestrator._parse_config` 1000×: 0.008246 s → 0.008115 s
- `Search.assess_source_credibility` 200×: 0.026464 s → 0.025423 s
- `StorageManager.persist_claim` 5×: 14.746 s → 14.576 s

Re-run these micro-benchmarks after substantial changes using similar workloads
to ensure performance remains within expected bounds.
