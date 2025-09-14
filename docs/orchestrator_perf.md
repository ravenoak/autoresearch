# Orchestrator performance

Benchmark executed on 2025-09-14 using:

```sh
uv run scripts/scheduling_resource_benchmark.py --max-workers 4 --tasks 100 \
    --arrival-rate 3 --service-rate 5 --mem-per-task 0.5
```

Empirical throughput across worker counts:

- 1 worker: ~795 tasks/s, CPU time 0.012 s.
- 2 workers: ~1563 tasks/s, CPU time 0.010 s.
- 3 workers: ~1763 tasks/s, CPU time 0.010 s.
- 4 workers: ~2811 tasks/s, CPU time 0.012 s.

These ranges show near-linear scaling up to two workers with diminishing
returns beyond that. Tests check for an improvement factor controlled by the
``SCHEDULER_SCALE_THRESHOLD`` environment variable, defaulting to 1.1.

Profiling uncovered a list rotation routine in `execution._rotate_list` that
allocated multiple intermediate lists. The implementation now uses
`itertools.islice` and `itertools.chain` to build the rotated sequence in a
single pass, reducing memory overhead for large agent lists.

## Scaling metrics

Running the new profiler option illustrates throughput scaling:

- 1 worker with profiling: ~804 tasks/s.
- 2 workers with profiling: ~1515 tasks/s.

## Tuning tips

- Use `profile=True` in `benchmark_scheduler` to capture cProfile stats and
  locate bottlenecks.
- Increase ``workers`` until throughput gains taper off.
- Adjust ``mem_per_task`` to model memory pressure; combine with profiling to
  observe how allocation affects scheduler efficiency.
