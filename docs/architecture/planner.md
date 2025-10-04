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
- Search instrumentation feeds the planner's telemetry audit: the legacy
  lookup path still records instance `add_calls` alongside vector counters so
  regression tests can assert parity across releases.
  【F:tests/unit/test_core_modules_additional.py†L363-L441】
- `QueryState.set_task_graph` merges planner telemetry into
  `state.metadata['planner']['telemetry']` and records a `planner.telemetry`
  React log entry containing task statistics and the latest snapshot.
- Existing telemetry such as planner confidence values are merged rather than
  overwritten, ensuring routing signals survive graph refreshes.

## Verification and retrieval integration

- PR5’s reverification loop extracts stored claims, retries audits with
  structured attempt metadata, and persists outcomes via
  `StorageManager.persist_claim`, ensuring planner telemetry aligns with the
  verification badges surfaced to clients.
  【F:src/autoresearch/orchestration/reverify.py†L73-L197】
  【F:tests/unit/orchestration/test_reverify.py†L1-L80】
- PR4’s retrieval upgrade exports GraphML and JSON artifacts with contradiction
  signals, allowing the planner to consume session graph availability flags
  while the gate monitors contradiction intensity.
  【F:src/autoresearch/knowledge/graph.py†L113-L204】
  【F:src/autoresearch/search/context.py†L618-L666】
  【F:src/autoresearch/orchestration/state.py†L1120-L1135】
- Behavior coverage locks audit badge propagation through the reasoning modes
  scenario so reverification status stays visible in planner metrics.
  【F:tests/behavior/features/reasoning_modes.feature†L8-L22】

```mermaid
flowchart TD
    Planner[Planner output] -->|TaskGraph| Coordinator
    Coordinator -->|QueryState.set_task_graph| State
    State -->|PR4 session graph flags| Retrieval
    Retrieval -->|GraphML/JSON exports|
        Storage[StorageManager.persist_claim]
    State -->|PR5 verification badge telemetry| Clients
    Storage -->|Persisted claims| Verification
    Verification -->|Audit badges| Clients
```

## Scheduling affinity

- `TaskCoordinator.schedule_next` orders pending tasks by readiness, whether a
  preferred tool matches the planner's affinity map, highest affinity score,
  dependency depth, pending dependency count, then task identifier.
- The deterministic ordering keeps scheduler behaviour reproducible while
  respecting the planner's intent about which tools should lead execution.
