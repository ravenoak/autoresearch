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

These simulations confirm that three critical failures trip the breaker and
that parallel merging preserves one claim per group regardless of scheduling
order.
