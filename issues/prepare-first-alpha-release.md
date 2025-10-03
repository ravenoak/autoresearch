# Prepare first alpha release

## Context
The September 30, 2025 Task CLI runs at 17:45:12 UTC (`task verify`) and
18:19:47 UTC (`task coverage`) both completed with the VSS loader streaming, the
CLI remediation banner in place, and the 92.4 % statement rate restored so the
alpha track can resume without `uv` wrappers.
【F:baseline/logs/task-verify-20250930T174512Z.log†L1-L23】【F:baseline/logs/task-coverage-20250930T181947Z.log†L1-L21】
We reopened this ticket to coordinate the remaining alpha release work: landing
the deep research initiative phases, capturing the end-to-end `task
release:alpha` sweep, and finalizing docs and packaging guidance before tagging.
`STATUS.md`, `TASK_PROGRESS.md`, `CODE_COMPLETE_PLAN.md`, and
`docs/release_plan.md` now cite the September 30 evidence so roadmap consumers
can follow the CLI and VSS remediation across the repository.
【F:STATUS.md†L21-L59】【F:TASK_PROGRESS.md†L1-L20】【F:CODE_COMPLETE_PLAN.md†L9-L33】【F:docs/release_plan.md†L18-L38】

After documenting the final-answer audit loop and operator acknowledgement
controls we captured the **14:28 UTC** `task verify` and **14:30 UTC**
`task coverage` reruns limited to the base extras. They exposed the standing
`QueryState.model_copy` and `A2AMessage` blockers while keeping the release
evidence trail current without triggering the deferred TestPyPI steps.
【F:docs/release_plan.md†L7-L20】【F:baseline/logs/task-verify-20250930T142820Z.log†L1-L36】
【F:baseline/logs/task-coverage-20250930T143024Z.log†L1-L41】
On **October 2, 2025 at 23:57 UTC** the repo-wide strict sweep completed without
errors, clearing the 2,114-item backlog from October 1. The status rollup,
release plan, task progress log, and code completion plan now cite the green
gate and note that Phase 2 planner work resumes once follow-up verify and
coverage sweeps stay green.
【F:baseline/logs/mypy-strict-20251002T235732Z.log†L1-L1】
【F:STATUS.md†L17-L24】【F:docs/release_plan.md†L16-L25】
【F:TASK_PROGRESS.md†L1-L12】【F:CODE_COMPLETE_PLAN.md†L9-L33】
On **October 1, 2025 at 14:39 UTC** a repo-wide `uv run mypy --strict src tests`
run reported 2,114 errors across 211 files, showing that the strict backlog now
resides inside analysis, integration, and behavior fixtures still expecting the
pre-expansion `EvaluationSummary` shape. The paired **14:40 UTC**
`uv run task coverage EXTRAS="nlp ui vss git distributed analysis llm parsers"`
run reached the unit suite before `QueryStateRegistry.register` hit the
`_thread.RLock` cloning failure in
`tests/unit/orchestration/test_orchestrator_auto_mode.py::`
`test_auto_mode_escalates_to_debate_when_gate_requires_loops`, so the coverage
gate continues to rely on the 92.4 % evidence while TestPyPI stays deferred.
【F:baseline/logs/mypy-strict-20251001T143959Z.log†L2358-L2377】
【F:baseline/logs/task-coverage-20251001T144044Z.log†L122-L241】

A **15:27 UTC** rerun of the coverage sweep now clears the registry cloning path
and fails when FastEmbed remains importable, leaving
`test_search_embedding_protocol_falls_back_to_encode` to assert that the
sentence-transformers fallback never loaded. The log captures the revised
failure mode while the TestPyPI hold and alpha gate remain in place until the
coverage fix lands.
【F:baseline/logs/task-coverage-20251001T152708Z.log†L60-L166】

The registry fix now deep-copies QueryState snapshots with typed memo support,
rehydrating `_thread.RLock` instances and preventing coverage regressions. The
new unit suite guards register, update, and round-trip flows while the 18:19 UTC
coverage log documents the restored 92.4 % gate we cite across the status
docs.
【F:src/autoresearch/orchestration/state_registry.py†L18-L148】
【F:tests/unit/orchestration/test_state_registry.py†L21-L138】
【F:baseline/logs/task-coverage-20250930T181947Z.log†L1-L21】

Search embedding fallback now honours the runtime configuration before
loading `sentence_transformers`, and the regression test confirms the encode
fallback activates when fastembed stays unavailable. The guard prevents fresh
coverage runs from tripping optional dependency imports while planner and
GraphRAG work resume.
【F:src/autoresearch/search/core.py†L147-L199】
【F:tests/unit/search/test_query_expansion_convergence.py†L154-L206】
On **September 30, 2025 at 15:15 UTC** we updated the `A2AMessage` schema to
accept the SDK's concrete payloads and introduced
`test_a2a_message_accepts_sdk_message` to guard the regression.
【F:src/autoresearch/a2a_interface.py†L66-L77】【F:src/autoresearch/a2a_interface.py†L269-L275】
【F:tests/unit/test_a2a_interface.py†L82-L90】
The focused unit run now passes with a real SDK message, the behavior suite
fails later on known orchestration and storage prerequisites instead of the
Pydantic validator, and the full coverage sweep still stalls while syncing GPU
extras in this environment.
【cfb7bf†L1-L2】【ab7ebf†L1-L13】【583440†L1-L29】

The **14:55 UTC** `task verify` sweep now clears the
`QueryState.model_copy` strict typing regression: `uv run mypy src` passes and
the run advances until it meets the known backlog of untyped test fixtures. The
log lives at `baseline/logs/task-verify-20250930T145541Z.log`, and a focused
`uv run mypy --strict` invocation over the registry and regression coverage file
confirms the gate stays green.
【F:baseline/logs/task-verify-20250930T145541Z.log†L1-L50】【df5aef†L1-L1】

For historical context, retain
`baseline/logs/task-verify-20250929T035829Z.log` when reviewing the verify
gate—the log shows the final red strict-typing wall in the HTTP layer before we
finished hardening the adapters and CLI. The Taskfile still passes optional
extras through to the embedded `task coverage` call so the configuration mirrors
the standalone sweep, but current gate reviews should prioritize the September
30 evidence now that the strict typing pipeline has recovered.
【F:baseline/logs/task-verify-20250929T035829Z.log†L1-L200】【F:Taskfile.yml†L360-L392】

The September 30, 2025 sweep at 19:04 UTC now completes `task release:alpha`
via the Task CLI, recording the recalibrated scout gate telemetry, CLI path
helper checks, and the refreshed 0.1.0a1 wheels. The verify, coverage, and
build logs are linked from the release plan, changelog, and status rollup so
auditors can trace the alpha evidence without leaving the repo.
【F:baseline/logs/task-verify-20250930T174512Z.log†L1-L23】【F:baseline/logs/task-coverage-20250930T181947Z.log†L1-L21】
【F:baseline/logs/python-build-20250929T030953Z.log†L1-L13】【F:CHANGELOG.md†L9-L20】

September 30, 2025 01:39 UTC: strict `mypy` over `src` and `tests` still
reports 3,911 historical errors, yet the missing-stub diagnostics for
`fastmcp`, `dspy`, and `PIL.Image` are gone now that the local shims mirror the
extras behaviour. The alpha gate can focus on annotation debt instead of stub
coverage during follow-up sweeps.【d423ea†L2995-L2997】

October 6, 2025: strict typing for the configuration loader, validators, and
Git stub now passes a targeted mypy sweep, unblocking the config milestone for
the alpha gate.【aa0591†L1-L2】

October 9, 2025: the HTTP API middleware and request state now expose explicit
types, and a dedicated mypy sweep plus integration coverage confirm the API
typing gap is closed ahead of the alpha tag.【F:src/autoresearch/api/middleware.py†L18-L169】【F:tests/integration/api/test_middleware_state.py†L1-L91】

## Tasks
- [x] Document the strict `mypy` regression and `EvaluationSummary` signature
  failure in `STATUS.md`, `TASK_PROGRESS.md`, `CODE_COMPLETE_PLAN.md`, and
  `docs/release_plan.md` using the **14:55 UTC** log for traceability.
- [x] Reconcile the deep research plan, performance guide, and pseudocode with
  the PRDV telemetry loop and new `EvaluationSummary` fields.
- [ ] Clear the strict typing backlog and restore coverage by updating the test
  fixtures and evaluation harness highlighted in
  `baseline/logs/task-verify-20250930T145541Z.log`.

## Dependencies
- [coordinate-deep-research-enhancement-initiative](coordinate-deep-research-enhancement-initiative.md)
- [adaptive-gate-and-claim-audit-rollout](adaptive-gate-and-claim-audit-rollout.md)
- [deliver-evidence-pipeline-2-0](deliver-evidence-pipeline-2-0.md)
- [planner-coordinator-react-upgrade](planner-coordinator-react-upgrade.md)
- [session-graph-rag-integration](session-graph-rag-integration.md)
- [evaluation-and-layered-ux-expansion](evaluation-and-layered-ux-expansion.md)
- [roll-out-layered-ux-and-model-routing](roll-out-layered-ux-and-model-routing.md)
- [build-truthfulness-evaluation-harness](build-truthfulness-evaluation-harness.md)
- [cost-aware-model-routing](cost-aware-model-routing.md)

## Acceptance Criteria
- Maintain traceability to the September 30, 2025 verify (17:45:12 UTC) and
  coverage (18:19:47 UTC) logs in `STATUS.md`, `TASK_PROGRESS.md`,
  `CODE_COMPLETE_PLAN.md`, and `docs/release_plan.md`, keeping coverage at or
  above the recorded 92.4 % rate.
- Record the October 2, 2025 strict pass in the same status surfaces and ensure
  planner Phase 2 delivery resumes only while the strict gate stays green.
- Document the 19:04 UTC `task release:alpha` sweep, ensuring verify, coverage,
  build, and packaging logs stay linked from `CHANGELOG.md`, the release plan,
  and this ticket for auditability.
- Confirm XPASS cleanup and Phase 1 of the deep research initiative remain
  archived in the release plan and deep research plan so the alpha gate reflects
  the current state of evidence.
- Lift the TestPyPI dry-run hold when the publish directive changes, capture the
  resulting log, and update `docs/release_plan.md` and `STATUS.md` before
  proposing the tag.
- Run the release sign-off review after the publish gate clears, documenting the
  decision and any deferred scope directly in this ticket.

## Status
Open
