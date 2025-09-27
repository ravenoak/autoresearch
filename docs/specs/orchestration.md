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

### Auto reasoning gate

`ReasoningMode.AUTO` begins with a single Synthesizer pass to produce a scout
answer. The orchestrator records the cycle metrics, evaluates the scout gate
policy, and either returns the direct answer or escalates to full debate with
`ReasoningMode.DIALECTICAL`. When debate proceeds the scout metadata is carried
into the new query state so downstream agents can reference the heuristics.

Operators can tune the gate policy through configuration or the CLI/UI:

- `core.gate_policy_enabled` toggles the policy entirely.
- `core.gate_retrieval_overlap_threshold`,
  `core.gate_nli_conflict_threshold`, and
  `core.gate_complexity_threshold` adjust exit heuristics.
- `core.gate_user_overrides` accepts JSON overrides to force exit/debate or
  pin specific heuristic scores.

### Planner task graph schema

`PlannerAgent` now emits a typed `TaskGraph` payload whose nodes include
`tools`, `depends_on`, `criteria`, and a numeric `affinity` mapping. The
planner still returns free-form rationale, yet the structured fields enable
deterministic scheduling. `QueryState.set_task_graph` normalises the payload,
coercing strings into lists, pruning missing dependencies, and recording any
adjustments as `planner.normalization` entries in `react_log`.

### Coordinator depth-affinity ordering

`TaskCoordinator` orders ready tasks by dependency depth and descending tool
affinity. A max-heap tie-breaker on task id preserves deterministic ordering
while downstream `react_traces` capture `unlock_events`, `task_depth`, and
`affinity_delta` metadata. Unlock events list every node whose dependencies are
resolved (including currently running tasks) so replay tooling can follow the
PRDV (plan, research, debate, validate) chain.

### ReAct telemetry replay

`QueryState.add_react_log_entry` and `record_planner_trace` persist planner
prompts, raw responses, structured graphs, and any normalisation warnings. The
`react_log` pairs with task-level traces to reconstruct planner intent,
coordinator unlocks, and tool affinity decisions without re-running models.

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
parallel aggregation. Unit tests exercise these properties and token
budgeting logic:

- [tests/unit/orchestration/test_circuit_breaker_thresholds.py][t13]
- [tests/unit/orchestration/test_circuit_breaker_determinism.py][t14]
- [tests/unit/orchestration/test_parallel_merge_invariant.py][t15]
- [tests/unit/orchestration/test_parallel_execute.py][t16]
- [tests/unit/orchestration/test_budgeting_algorithm.py][t17]

## Traceability

- Modules
  - [src/autoresearch/orchestration/][m1]
  - [docs/algorithms/orchestration.md][d1]
  - [scripts/orchestration_sim.py][s1]

[m1]: ../../src/autoresearch/orchestration/
[d1]: ../../docs/algorithms/orchestration.md
[s1]: ../../scripts/orchestration_sim.py
[t13]: ../../tests/unit/orchestration/test_circuit_breaker_thresholds.py
[t14]: ../../tests/unit/orchestration/test_circuit_breaker_determinism.py
[t15]: ../../tests/unit/orchestration/test_parallel_merge_invariant.py
[t16]: ../../tests/unit/orchestration/test_parallel_execute.py
[t17]: ../../tests/unit/orchestration/test_budgeting_algorithm.py

