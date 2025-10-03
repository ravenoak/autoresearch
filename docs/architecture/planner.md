# Planner Telemetry Contract

The planner emits structured JSON so downstream components can schedule and
audit tasks without ad-hoc adapters. The contract aligns the language model
output with `TaskGraph`'s native schema while capturing top-level objectives
and exit criteria for reporting.

## Structured output schema

- `PlannerPromptBuilder` requests task `id`, `question`, `sub_questions`,
  `tools`, numeric `affinity`, dependency lists, and completion `criteria`.
- Tool scores must be floats in `[0, 1]`; the planner may provide aliases such
  as `objectives` or `exit_criteria`, which are normalised into the canonical
  fields.
- Top-level `objectives`, `exit_criteria`, and a free-form `explanation` live
  alongside the task list so telemetry consumers can reason about plan intent.

## Telemetry flow

- `TaskGraph.from_planner_output` accepts JSON strings, mappings, or sequences
  and produces a `TaskGraph` with canonical task nodes plus preserved
  objectives, exit criteria, and explanations.
- `QueryState.set_task_graph` merges planner telemetry into
  `state.metadata['planner']['telemetry']` and records a `planner.telemetry`
  React log entry containing task statistics and the latest snapshot.
- Existing telemetry such as planner confidence values are merged rather than
  overwritten, ensuring routing signals survive graph refreshes.

## Scheduling affinity

- `TaskCoordinator.schedule_next` orders pending tasks by readiness, whether a
  preferred tool matches the planner's affinity map, highest affinity score,
  dependency depth, pending dependency count, then task identifier.
- The deterministic ordering keeps scheduler behaviour reproducible while
  respecting the planner's intent about which tools should lead execution.
