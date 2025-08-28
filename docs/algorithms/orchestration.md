# Orchestration

This note formalizes simulations for the circuit breaker and parallel
execution.

## Circuit breaker simulation

1. Each agent tracks a breaker state with a failure count, last failure
   time, current mode, and recovery attempts.
2. Critical or recoverable errors add 1 to the failure count; transient
   errors add 0.5.
3. When the count reaches the threshold, the breaker opens and rejects
   requests.
4. After the cooldown passes, the breaker moves to half-open. The next
   success closes it and resets counters.

Pseudo-code:

```
for event in events:
    if event in {"critical", "recoverable"}:
        failures += 1
    else:
        failures += 0.5
    if failures >= threshold and state == "closed":
        state = "open"
    if state == "open" and now - last_failure > cooldown:
        state = "half-open"
on_success():
    if state == "half-open":
        state = "closed"
        failures = 0
    else:
        failures = max(0, failures - 1)
```

### Proof of breaker threshold

- Start with failure count ``f = 0`` and state ``closed``.
- After each critical error ``f`` increments by one.
- After the third critical error ``f = 3`` so ``f >= threshold`` and the
  state flips to ``open``.
- No further attempts succeed until ``now - last_failure > cooldown``. At that
  moment ``update_circuit_breaker`` sets the state to ``half-open``.
- A subsequent success triggers ``handle_agent_success`` which resets
  ``f = 0`` and returns the state to ``closed``.

### Determinism and error recovery

- The function ``simulate_circuit_breaker`` advances a fake clock one
  step per event. ``tick`` events move time forward without mutating
  state, allowing cooldown periods to be modelled deterministically.
- Replaying the same event sequence yields identical state transitions
  because the manager depends only on the ordered events and the clock
  value.
- After the breaker opens, a ``tick`` followed by any error event moves
  the state to ``half-open`` once the cooldown passes. A final
  successful event closes the breaker and resets counters.

## Parallel execution simulation

1. Agent groups run in a thread pool with at most ``cpu_count - 1``
   workers.
2. Each group uses the orchestrator to produce a response. Errors and
   timeouts are recorded.
3. Completed group results update a shared query state in the order they
   finish.
4. A synthesizer aggregates the state into a final response.

Pseudo-code:

```
with ThreadPoolExecutor(max_workers):
    for group in agent_groups:
        submit(run_group, group)
    for future in as_completed(futures):
        collect_result(future, state)

aggregate = Synthesizer.execute(state)
return state.synthesize()
```

### Proof of merging invariant

- Each group emits exactly one claim ``c_i``.
- ``as_completed`` may return groups in any order ``p``.
- For every finished group ``collect_result`` appends ``c_i`` to the shared
  state. Appending is order-independent for set membership.
- The final state therefore contains the set ``{c_1, ..., c_n}`` regardless of
  ``p``. Each claim appears once because no group is processed twice.

These simulations confirm that three critical failures trip the breaker and
that parallel merging preserves one claim per group regardless of scheduling
order.

### Reference implementations

- Unit test `tests/unit/orchestration/test_circuit_breaker_thresholds.py`
  validates the breaker threshold and recovery sequence.
- Unit test `tests/unit/orchestration/test_circuit_breaker_determinism.py`
  demonstrates deterministic replay and cooldown recovery.
- Unit test `tests/unit/orchestration/test_parallel_merge_invariant.py`
  exercises the merging invariant under concurrent execution.
- Unit test `tests/unit/orchestration/test_parallel_execute.py`
  covers mixed success, error, and timeout paths.

### Assumptions

- Each agent group contributes a unique claim string.
- Results are merged into a dictionary keyed by joined group labels so
  insertion order does not affect membership.
