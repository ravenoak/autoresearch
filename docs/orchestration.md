# Orchestration Workflow

The orchestration layer coordinates planning, task execution, and synthesis
while retaining thread safety and reproducible telemetry.

- Every query instantiates a dedicated `QueryState`. Updates are guarded by a
  re-entrant lock so agents cannot interleave writes.
- Planner output is normalised into a typed task graph. The upgraded
  `PlannerPromptBuilder` now asks for `socratic_checks`,
  `dependency_depth`, `dependency_rationale`, and a top-level
  `dependency_overview`. These are preserved on the `TaskNode`
  structure so downstream schedulers can reason about critical paths.
- Planner metadata (for example `metadata.version`, `metadata.notes`, and
  planner-specified tags) is normalised into JSON-safe dictionaries. The
  metadata is surfaced through `result.metadata['task_graph']` so downstream
  services can reason about planner intent without re-parsing the raw plan.
- `QueryState.set_task_graph` captures planner telemetry, aggregating the
  objectives, exit criteria, and per-task affinity/explanation data. The
  telemetry is serialisation-safe and restored with the state.
- `TaskCoordinator` converts planner payloads into `TaskGraphNode` snapshots.
  Nodes sort by readiness, affinity, planner-provided dependency depth, then
  identifier. Every ReAct step records the scheduler snapshot with the
  Socratic prompts, dependency rationale, and selected depth so downstream
  tools can replay the decision trail. Coordinator telemetry now echoes
  `task_metadata` alongside scheduler candidates to preserve planner hints
  such as priority or budgets.
- Planner and coordinator metadata flow into the `react_log`, agent results,
  and behaviour scenarios for observability.
- Scout gate telemetry records `coverage_ratio`, aggregated
  `scout_agreement` statistics (score, sample count, min, and max), and a
  normalized `decision_outcome` so dashboards can chart debate versus
  scout-only exits without replaying runs.

## PRDV verification loop

- The PRDV (plan, research, debate, validate) loop captures planner prompts,
  tool routing, and validation telemetry in a single trace. Planner
  Socratic cues identify risky assumptions, while the dependency overview
  documents the critical path for each cycle. Coordinated ReAct steps append
  unlock events, affinity deltas, and the planner-provided rationale so the
  verification trail can be replayed without re-running agents.
- During the debate and validate phases, coordinator metadata references the
  planner depth budget. Tasks promoted to debate must include Socratic self
  checks that describe how contradictions will be resolved or escalated.
- QueryState metadata records the dependency overview and PRDV loop count
  under `metadata['planner']['telemetry']`, making it available to dashboards
  and behaviour suites.

## Error handling

- `_handle_agent_error` now emits diagnostic claims with a `debug` mapping that
  captures the agent name, error class, recovery category, and the selected
  recovery strategy. The orchestrator appends the same payload to
  `state.metadata['errors']` so response metrics expose `telemetry.claim_debug`
  for downstream dashboards.
- Recovery strategies (`retry_with_backoff`, `fallback_agent`, and
  `fail_gracefully`) stamp `recovery_suggestion` metadata and update claims with
  `type="diagnostic"` and `subtype` matching the error category. Downstream
  synthesizers can therefore separate user-facing messages from troubleshooting
  breadcrumbs.
- Parallel execution injects identical diagnostic claims for failures and
  timeouts. Each claim lists the affected agent group, the event (`error` or
  `timeout`), and timeout thresholds when applicable, making fleet health
  reviews consistent across sequential and parallel flows.
