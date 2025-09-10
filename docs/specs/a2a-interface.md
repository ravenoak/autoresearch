# A2A Interface

## Overview

A2A (Agent-to-Agent) interface for Autoresearch.

## Algorithms

- Implement core behaviors described above.

## Invariants

- Preserve documented state across operations.
- Each task is dispatched exactly once.
- Agent state updates occur atomically.
- No agent handles more than one task at a time.
- The total dispatched count equals the sum of per-agent counts.

## Proof Sketch

A global lock guards the shared dispatch map. Each operation acquires the
lock, updates the map, and releases the lock before the next dispatch.
Mutual exclusion prevents lost updates and duplicate assignments, so the
invariants hold. The simulation [a2a_concurrency_sim.py][s1] exercises the
interface with concurrent threads and yields consistent counts across
agents.

## Simulation

Run the simulation to observe race-free dispatch:

```
uv run scripts/a2a_concurrency_sim.py --agents 3 --tasks 5
```

The result reports per-agent counts and a total equal to the number of
submitted tasks. For broader concurrency context, see
[distributed.md](distributed.md).

## Traceability


- Modules
  - [src/autoresearch/a2a_interface.py][m1]
- Simulations
  - [scripts/a2a_concurrency_sim.py][s1]
- Tests
  - [tests/behavior/features/a2a_interface.feature][t1]
  - [tests/integration/test_a2a_interface.py][t2]
  - [tests/unit/test_a2a_interface.py][t3]
  - [tests/unit/test_a2a_concurrency_sim.py][t4]

[m1]: ../../src/autoresearch/a2a_interface.py
[s1]: ../../scripts/a2a_concurrency_sim.py
[t1]: ../../tests/behavior/features/a2a_interface.feature
[t2]: ../../tests/integration/test_a2a_interface.py
[t3]: ../../tests/unit/test_a2a_interface.py
[t4]: ../../tests/unit/test_a2a_concurrency_sim.py
