# Orchestration Workflow

The orchestration layer coordinates planning, task execution, and synthesis
while retaining thread safety and reproducible telemetry.

- Every query instantiates a dedicated `QueryState`. Updates are guarded by a
  re-entrant lock so agents cannot interleave writes.
- Planner output is normalised into a typed task graph. The new
  `PlannerPromptBuilder` instructs the LLM to emit JSON including
  `objectives`, `tool_affinity`, `exit_criteria`, and `explanation` for each
  task. These fields are mapped onto the runtime `TaskNode` data structure.
- `QueryState.set_task_graph` captures planner telemetry, aggregating the
  objectives, exit criteria, and per-task affinity/explanation data. The
  telemetry is serialisation-safe and restored with the state.
- `TaskCoordinator` converts planner payloads into `TaskGraphNode` snapshots.
  Nodes sort by readiness, affinity, dependency depth, then identifier. Every
  ReAct step records the scheduler snapshot so downstream tools can replay the
  decision trail.
- Planner and coordinator metadata flow into the `react_log`, agent results,
  and behaviour scenarios for observability.

## Socratic Q/A

- **Question:** How do we know the scheduler prefers actionable tasks rather
  than deep dependency chains?
- **Answer:** We inspect the telemetry snapshots. Ready tasks bubble to the top
  of each `scheduler.candidates` list, and coordinator decisions persist across
  serialisation, confirming the readiness-first ordering.
