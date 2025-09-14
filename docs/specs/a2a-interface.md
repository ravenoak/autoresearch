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
- A monotonically increasing event id yields a total order of dispatches.
- The dispatch log length equals the total number of dispatched tasks.

## Proof Sketch

A global lock guards the shared dispatch map and a monotonically increasing
event counter. Each operation acquires the lock, updates the map and counter,
records the event, and releases the lock before the next dispatch. Threads
cannot interleave inside the critical section, so increments of the per-agent
count, the global total, and the event log are atomic. This eliminates race
conditions and yields a total order over dispatches. Under these conditions
the invariants hold:

- totals are preserved because each task increments the counts exactly once,
- agents never see the same task twice,
- no agent handles multiple tasks concurrently, and
- the event log reflects a single global ordering.

The simulation `a2a_concurrency_sim.py` schedules concurrent threads and
confirms that observed counts and event ordering match expectations. For
algorithmic context see [algorithms/a2a_interface.md][a1].

## Simulation

Run the simulation to observe race-free dispatch and ordered events:

```
uv run scripts/a2a_concurrency_sim.py --agents 3 --tasks 5
```

The result reports per-agent counts, a total equal to the number of submitted
tasks, and a dispatch log enumerating the global event order. The log is
sorted by event id without gaps or duplicates, proving mutual exclusion.
For broader concurrency context, see [distributed.md](distributed.md).

## Simulation Expectations

Unit tests assert that:

- totals match the sum of per-agent counts,
- each agent receives exactly ``tasks`` assignments,
- the dispatch log is already sorted by event id, and
- the number of log entries equals the dispatched total.

[a1]: ../algorithms/a2a_interface.md
