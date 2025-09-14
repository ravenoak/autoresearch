# Orchestrator performance

Benchmark executed on 2025-09-11 using:

```sh
uv run scripts/scheduling_resource_benchmark.py --max-workers 4 --tasks 100 \
    --arrival-rate 3 --service-rate 5 --mem-per-task 0.5
```

Results showed increasing throughput as workers scaled:

- 1 worker: ~846 tasks/s, CPU time 0.012 s.
- 2 workers: ~1665 tasks/s, CPU time 0.012 s.
- 3 workers: ~2426 tasks/s, CPU time 0.008 s.
- 4 workers: ~3179 tasks/s, CPU time 0.010 s.

Profiling uncovered a list rotation routine in `execution._rotate_list`
that allocated multiple intermediate lists. The implementation now uses
`itertools.islice` and `itertools.chain` to build the rotated sequence in a
single pass, reducing memory overhead for large agent lists.
