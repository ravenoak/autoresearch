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

Formally, the breaker is a deterministic finite state machine with
states ``S = {closed, open, half-open}`` and transition function
``\delta(s, e, t)``.  The function examines the current state ``s``, the
incoming event ``e``, and the clock ``t``.  Because ``\delta`` is pure
and the time steps are explicit, applying the same event sequence always
produces the same state trajectory.

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

Let ``C_i`` denote the claim set returned by group ``i``.  The update
step computes ``U := U \cup C_i`` for each finished group.  Set union is
associative and commutative, so the order in which groups finish does
not affect the final ``U``.  Determinism therefore follows from the
functional nature of ``collect_result`` and the absence of shared mutable
state outside ``U``.

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

## Token budgeting simulation

1. Start with a budget ``b`` and a query of ``q`` tokens.
2. If the orchestration loops ``l`` times, divide ``b`` by ``l`` to
   distribute tokens across loops.
3. Clamp the budget to ``[q + buffer, q * f]`` where ``f`` is the adaptive
   maximum factor and ``buffer`` a safety margin.
4. The adjusted budget bounds token usage while scaling with query size and
   loop count.

Pseudo-code:

```
budget //= max(1, loops)
budget = min(budget, q * factor)
budget = max(budget, q + buffer)
```

### Proof of bounds

- Division by ``max(1, l)`` ensures each loop receives at most ``b / l``
  tokens.
- The ``min`` operation caps usage at ``q * f``, so the budget never exceeds
  the scaled query length.
- The ``max`` operation enforces a floor of ``q + buffer`` when the initial
  budget is too small.
- Therefore the final budget lies in ``[q + buffer, q * f]`` and the sum of
  per-loop allocations does not exceed ``b``.

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
- Script `scripts/orchestration_sim.py` replays both simulations to
  demonstrate deterministic behavior.

### Assumptions

- Each agent group contributes a unique claim string.
- Results are merged into a dictionary keyed by joined group labels so
  insertion order does not affect membership.
