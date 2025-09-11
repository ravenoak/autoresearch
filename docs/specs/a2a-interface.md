# A2A Interface

## Overview

A2A (Agent-to-Agent) interface for Autoresearch.

## Algorithms

- Implement core behaviors described above. See
  [algorithms/a2a_interface.md][a1] for protocol flow and security notes.

## Invariants

- Preserve documented state across operations.
- Each task is dispatched exactly once.
- Agent state updates occur atomically.
- No agent handles more than one task at a time.
- The total dispatched count equals the sum of per-agent counts.

## Proof Sketch

A global lock guards the shared dispatch map. Each operation acquires the
lock, updates the map, and releases the lock before the next dispatch.
Threads cannot interleave inside the critical section, so every increment
of the per-agent count and the global total is atomic. Under these
conditions the invariants hold:

- totals are preserved because each task increments the counts exactly once,
- agents never see the same task twice, and
- no agent handles multiple tasks concurrently.

The simulation [a2a_concurrency_sim.py][s1] schedules concurrent threads and
confirms that observed counts match expectations. For algorithmic context see
[algorithms/a2a_interface.md][a1].

## Simulation

Run the simulation to observe race-free dispatch:

```
uv run scripts/a2a_concurrency_sim.py --agents 3 --tasks 5
```

The result reports per-agent counts and a total equal to the number of
submitted tasks. For broader concurrency context, see
[distributed.md](distributed.md).

## Simulation Expectations

Unit tests cover message handling and concurrency safeguards.

## Traceability


- Modules
  - [src/autoresearch/a2a_interface.py][m1]
  - [docs/algorithms/a2a_interface.md][a1]
- Simulations
  - [scripts/a2a_concurrency_sim.py][s1]
- Tests
  - [tests/behavior/features/a2a_interface.feature][t1]
  - [tests/integration/test_a2a_interface.py][t2] – verifies three
    concurrent queries complete without blocking.
  - [tests/unit/test_a2a_interface.py][t3] – checks three parallel
    queries return distinct results.
  - [tests/unit/test_a2a_concurrency_sim.py][t4]

[m1]: ../../src/autoresearch/a2a_interface.py
[a1]: ../algorithms/a2a_interface.md
[s1]: ../../scripts/a2a_concurrency_sim.py
[t1]: ../../tests/behavior/features/a2a_interface.feature
[t2]: ../../tests/integration/test_a2a_interface.py
[t3]: ../../tests/unit/test_a2a_interface.py
[t4]: ../../tests/unit/test_a2a_concurrency_sim.py
