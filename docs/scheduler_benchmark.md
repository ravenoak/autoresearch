# Scheduler Resource Benchmark

This benchmark measures CPU and memory impact of the backup scheduler.

## Methodology

- Patch the backup creation routine to a no-op to isolate scheduler overhead.
- Start the scheduler with a one-second interval and run for a short duration.
- Measure CPU time and resident memory before and after using
  `resource.getrusage`.

CPU time is computed as:

```
cpu_time = end.ru_utime - start.ru_utime
```

Memory use is calculated with:

```
mem_kb = end.ru_maxrss - start.ru_maxrss
```

## Results and Tuning

The test [test_scheduler_benchmark.py](../tests/unit/test_scheduler_benchmark.py)
reports measured CPU and memory. Rising values suggest increasing the backup
interval or optimizing the backup routine.
