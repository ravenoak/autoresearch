# Orchestration Module Specification

## Overview

The orchestration package (`src/autoresearch/orchestration/`) coordinates
agents and reasoning loops. It manages agent rotation, state transfer and
error handling while providing detailed logging and token counting.

The following properties derive from the simulations in
[docs/algorithms/orchestration.md][d1].

## Algorithms

### Circuit breaker finite state machine

The breaker has states `closed`, `open`, and `half-open`. Errors increment a
failure counter: critical and recoverable errors add `1` while transient
errors add `0.5`. When the counter reaches the threshold (default `3`) the
state moves from `closed` to `open`. After the cooldown elapses the breaker
enters `half-open` and the next success returns it to `closed` with counters
reset.

### Token-budget allocation

Given an initial budget `b` for a query of `q` tokens and `l` orchestration
loops, the budget is divided by `max(1, l)` then clamped to `[q + buffer,
q * factor]`. The lower bound guarantees enough tokens for the query plus a
margin while the upper bound scales with input size and prevents overruns.

## Invariants

### Parallel merge

Agent groups execute in a thread pool and update shared query state as each
group finishes. Each group contributes a claim set `C_i` and the updater
performs `U = U ∪ C_i`. Set union's associativity and commutativity ensure
the final `U` contains every claim regardless of completion order. No group
updates the state twice, preventing duplicates.

### Deterministic breaker

The transition function is pure and depends only on the ordered event
sequence and clock, so identical inputs yield identical state trajectories.

## Proof Sketch

### Breaker thresholds

Start with failure count `f = 0` in the `closed` state. Each critical error
adds one to `f`. After three critical errors `f = 3` meets the threshold and
opens the breaker. No calls proceed until the cooldown passes. A subsequent
success in `half-open` resets `f` to zero and closes the breaker.

### Merging determinism

Let each group emit one unique claim. `as_completed` may return groups in any
order, yet each result is merged once via set union. Because union is order
independent and side-effect free, replaying the same completion order yields
the same aggregate state.

## Simulation Expectations

`scripts/orchestration_sim.py` demonstrates deterministic breaker recovery and
parallel aggregation.

[d1]: ../algorithms/orchestration.md

