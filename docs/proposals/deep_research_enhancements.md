# Deep research enhancements

The orchestration gate now calls
[`Orchestrator.evaluate_scout_gate_policy`][orchestrator-policy] which defers to
[`ScoutGatePolicy.evaluate`][policy-evaluate] for loop reduction decisions. This
proposal tracks the remaining work needed to feed those evaluators with scout
metrics gathered during retrieval.

- Instrument the scout pass so retrieval overlap, entailment conflict, and
  query complexity features flow into `QueryState.metadata['scout_*']` before
  debate. The policy consumes these fields directly.
- Surface the telemetry expected by the gate (see acceptance criteria) so the
  orchestrator can log when debate loops are reduced and why.

## Implementation sketch

- Extend the search pipeline to emit backend-specific retrieval sets and
  lightweight entailment scores before the debate phase begins.
- Update `SearchContext` with helpers that cache the latest scout metrics and
  populate the orchestration state automatically.
- Ensure the orchestrator invokes those helpers right before evaluating the
  scout gate.

## Acceptance criteria

- Retrieval set overlap, entailment conflict scores, and complexity features are
  filled automatically on `QueryState.metadata` when the gate runs.
- Telemetry exposes the target loop count, decision reason, heuristic inputs,
  and estimated tokens saved whenever the gate runs.
- Unit coverage exercises the scout pipeline end to end, verifying that real
  retrieval observations drive the gate instead of synthetic metadata fixtures.

[orchestrator-policy]: ../../src/autoresearch/orchestration/orchestrator.py
[policy-evaluate]: ../../src/autoresearch/orchestration/orchestration_utils.py
