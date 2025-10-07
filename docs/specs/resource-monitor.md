# Resource Monitor

## Overview

Background resource usage monitoring utilities. See
[resource monitor algorithm][rm] for sampling details.

## Sampling Frequency

Sampling frequency `f` adapts to CPU load `L` using a linear scale:

- `f = min(f_max, f_base * (1 + L / L_thresh))`
- `interval = 1 / f`

`f_base` is the baseline rate and `L_thresh` defines when adjustments begin.

## Resource Thresholds

Thresholds use recent statistics to detect spikes:

- `T_cpu = μ_cpu + k * σ_cpu`
- `T_mem = μ_mem + k * σ_mem`

`μ` is the mean, `σ` the standard deviation, and `k = 2` for a two-sigma limit.

## Load Spike Response

```pseudo
loop:
    cpu, mem = sample_usage()
    f = min(f_max, f_base * (1 + cpu / L_thresh))
    if cpu > T_cpu or mem > T_mem:
        log("spike", cpu=cpu, mem=mem)
    sleep(1 / f)
```

## Algorithms

- Implement core behaviors described above.

## Invariants

- Preserve documented state across operations.

## Proof Sketch

Core routines enforce invariants by validating inputs and state. The
formula [resource_monitor_bounds.py][sim] derives expected sampling
intervals and thresholds.

## Simulation Expectations

Unit tests cover nominal and edge cases for these routines.

## Traceability


- Modules
  - [src/autoresearch/resource_monitor.py][m1]
- Tests
  - [tests/integration/test_monitor_metrics.py][t81]
  - [tests/unit/legacy/test_main_monitor_commands.py][t82]
  - [tests/unit/legacy/test_monitor_cli.py][t83]
  - [tests/unit/legacy/test_monitor_metrics_init.py][t84]
  - [tests/unit/legacy/test_node_health_monitor_property.py][t85]
  - [tests/unit/legacy/test_resource_monitor_gpu.py][t99]
  - [tests/unit/legacy/test_system_monitor.py][t86]

[m1]: ../../src/autoresearch/resource_monitor.py
[rm]: ../algorithms/resource_monitor.md
[sim]: ../../scripts/resource_monitor_bounds.py

[t81]: ../../tests/integration/test_monitor_metrics.py
[t82]: ../../tests/unit/legacy/test_main_monitor_commands.py
[t83]: ../../tests/unit/legacy/test_monitor_cli.py
[t84]: ../../tests/unit/legacy/test_monitor_metrics_init.py
[t85]: ../../tests/unit/legacy/test_node_health_monitor_property.py
[t99]: ../../tests/unit/legacy/test_resource_monitor_gpu.py
[t86]: ../../tests/unit/legacy/test_system_monitor.py
