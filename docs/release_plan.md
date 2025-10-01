# Release Plan

This document outlines the upcoming release milestones for **Autoresearch**.
Dates are aspirational and may shift as development progresses.
The publishing workflow follows the steps in
[deployment.md](deployment.md). Detailed release commands are documented in
[releasing.md](releasing.md). See
[installation.md](installation.md) for environment setup and
ROADMAP.md for high-level milestones.

The project kicked off in **May 2025** (see the initial commit dated
`2025-05-18`). This schedule was last updated on **September 24, 2025** and
reflects that the codebase currently sits at the **unreleased 0.1.0a1** version
defined in `autoresearch.__version__`. The project targets **0.1.0a1** for
**September 15, 2026** and **0.1.0** for **October 1, 2026**. See
STATUS.md, ROADMAP.md, and CHANGELOG.md for aligned progress. Phase 3
(stabilization/testing/documentation) and Phase 4 activities remain planned.

## Status

The **October 1, 2025 at 14:39 UTC** repo-wide `mypy --strict` sweep records
2,114 errors across 211 files, underscoring that the remaining strict backlog
now lives almost entirely inside legacy analysis, integration, and behavior
fixtures. The run confirms that the new import shims keep the gate executing,
but the typed evaluation harness and planner fixtures must still absorb the
`EvaluationSummary` expansion before the count can fall. The paired
**14:40 UTC** `task coverage` attempt reaches the unit suite before the
`QueryStateRegistry.register` call hits the `_thread.RLock` cloning failure
captured in the earlier verify logs. Coverage therefore halts in
`test_auto_mode_escalates_to_debate_when_gate_requires_loops`, leaving the
statement rate unchanged while we continue to defer the TestPyPI dry run per
the alpha directive.
【F:baseline/logs/mypy-strict-20251001T143959Z.log†L2358-L2377】
【F:baseline/logs/task-coverage-20251001T144044Z.log†L122-L241】

The **September 30, 2025 at 14:55 UTC** `task verify` sweep now reaches
`mypy --strict` before failing on 118 untyped test fixtures and the
`EvaluationSummary` constructor, which expects planner depth and routing
metrics. Until those annotations and harness updates land, the strict gate stays
red and coverage remains at risk even though the prior 92.4 % log is still the
latest green record.
【F:baseline/logs/task-verify-20250930T145541Z.log†L1-L120】
【F:baseline/logs/task-verify-20250930T145541Z.log†L2606-L2617】

The **September 30, 2025 at 14:28 UTC** `task verify` rerun recorded after the
final-answer audit documentation now halts in the existing
`QueryState.model_copy` strict-typing gap while the new `audit.*` policy knobs
settle into the registry. On **September 30, 2025 at 15:15 UTC** we patched the
`A2AMessage` schema to accept the SDK's concrete messages and added
`test_a2a_message_accepts_sdk_message` so a regression test guards the fix.
【F:baseline/logs/task-verify-20250930T142820Z.log†L1-L36】【F:src/autoresearch/a2a_interface.py†L66-L77】
【F:src/autoresearch/a2a_interface.py†L269-L275】【F:tests/unit/test_a2a_interface.py†L82-L90】
The dedicated unit run confirms a real SDK envelope now validates, while the
behavior suite no longer surfaces the prior Pydantic failure and instead stops
on pre-existing orchestration and storage prerequisites.
【cfb7bf†L1-L2】【ab7ebf†L1-L13】
The full coverage sweep still stalls while attempting to install GPU extras in
this environment, so we retain the earlier **14:30 UTC** coverage log as the
latest complete evidence until the extras sync can succeed.
【583440†L1-L29】【F:baseline/logs/task-coverage-20250930T143024Z.log†L1-L41】

The **September 30, 2025 at 14:55 UTC** verify sweep still clears
`QueryState.model_copy`, yet the same log captures the untyped test backlog and
the `EvaluationSummary` call failure noted above. The registry-specific
`mypy --strict` probe remains green, so the blocking work now lives entirely in
the shared fixtures and harness.
【F:baseline/logs/task-verify-20250930T145541Z.log†L1-L120】
【F:baseline/logs/task-verify-20250930T145541Z.log†L2606-L2617】
【df5aef†L1-L1】

The **September 30, 2025 at 19:04 UTC** sweep completed `task release:alpha`
end-to-end. `task verify` and `task coverage` captured the recalibrated scout
gate telemetry, CLI path helper checks, and the 92.4 % coverage rate, while the
packaging stage produced fresh 0.1.0a1 wheels and sdists. The updated alpha
ticket now links the verify, coverage, and build logs for traceability.
【F:baseline/logs/task-verify-20250930T174512Z.log†L1-L23】【F:baseline/logs/task-coverage-20250930T181947Z.log†L1-L21】
【F:baseline/logs/python-build-20250929T030953Z.log†L1-L13】【F:issues/prepare-first-alpha-release.md†L1-L34】

Reviewers auditing the current verify gate should inspect
`baseline/logs/task-verify-20250929T173615Z.log`, which advances through
`flake8` before surfacing 93 strict typing errors across 28 modules,
including the HTTP session adapters, evaluation harness, Streamlit CLI, and
distributed executor protocols. Coverage remains blocked until those fixes
land. The follow-up coverage attempt at 17:37 UTC synced every non-GPU
optional extra and began the unit matrix, but the log at
`baseline/logs/task-coverage-20250929T173738Z.log` stops at the unit
coverage check for `tests/unit/test_additional_coverage.py`
(`test_render_evaluation_summary_joins_artifacts`) after a manual interrupt
at roughly 10 % progress. The CLI summary table now defaults planner depth and
routing telemetry to em-dash placeholders when the harness omits those metrics,
and a regression fixture exercises the populated columns so coverage stays
aligned with the printed output.[cli-summary-formatting][coverage-fixture]
The refreshed behavior scenario renders both a populated row and a
telemetry-empty row, ensuring the CLI output stays synchronized with the
expanded schema while the unit fixture validates the same fallbacks for the
render helper.[bdd-evaluation-steps][coverage-fixture]
The TestPyPI dry run stays deferred under the release directive while we clear
the strict typing wall and unblock the coverage sweep.
【F:baseline/logs/task-verify-20250929T173615Z.log†L50-L140】
【F:baseline/logs/task-coverage-20250929T173738Z.log†L1-L120】
【F:baseline/logs/task-coverage-20250929T173738Z.log†L220-L225】
【F:baseline/logs/release-alpha-20250929T000814Z.summary.md†L3-L12】

Deep research tickets stay referenced for release sign-off:

- **Phase 1 – Adaptive gate and claim audits:** See
  [adaptive-gate-and-claim-audit-rollout][phase1-ticket] for the gating
  heuristics, scout pass, audit tables, and the new answer auditor that hedges
  unsupported claims after a targeted re-retrieval pass.
- **Phase 2 – Planner and coordinator upgrades:**
  [planner-coordinator-react-upgrade][phase2-ticket] records the ReAct
  telemetry and scheduling refinements.
- **Phase 3 – Session GraphRAG integration:**
  [session-graph-rag-integration][phase3-ticket] covers graph ingestion,
  contradiction checks, and telemetry.
- **Phase 4 – Evaluation harness and layered UX:**
  [evaluation-and-layered-ux-expansion][phase4-ticket] captures the
  TruthfulQA automation and multi-layer interface work.
- **Phase 5 – Cost-aware model routing:**
  [cost-aware-model-routing][phase5-ticket] details the budget-aware routing,
  telemetry, and tuning guides.

These references align with the acceptance criteria in
[prepare-first-alpha-release][prepare-alpha].

[phase1-ticket]: ../issues/archive/adaptive-gate-and-claim-audit-rollout.md
[phase2-ticket]: ../issues/planner-coordinator-react-upgrade.md
[phase3-ticket]: ../issues/session-graph-rag-integration.md
[phase4-ticket]: ../issues/evaluation-and-layered-ux-expansion.md
[phase5-ticket]: ../issues/cost-aware-model-routing.md
[prepare-alpha]: ../issues/prepare-first-alpha-release.md
[scout-gate-test]: ../tests/unit/orchestration/test_gate_policy.py
[cli-summary-formatting]: ../src/autoresearch/cli_utils.py#L300-L347
[coverage-fixture]: ../tests/unit/test_additional_coverage.py#L160-L236
[bdd-evaluation-steps]: ../tests/behavior/steps/evaluation_steps.py#L1-L200

The **September 30, 2025 at 18:19 UTC** sweeps confirm the Task CLI exposes
`verify` and `coverage` again. The 17:45 UTC verification run covers linting,
typing, and all suites with the VSS loader streaming, while the 18:19 UTC
coverage run holds the ≥90 % gate and logs the CLI remediation banner. The new
evidence lives at `baseline/logs/task-verify-20250930T174512Z.log` and
`baseline/logs/task-coverage-20250930T181947Z.log`, replacing the prior
regression logs and documenting the cleared CLI and VSS blockers.
【F:baseline/logs/task-verify-20250930T174512Z.log†L1-L23】
【F:baseline/logs/task-coverage-20250930T181947Z.log†L1-L21】

The **September 28, 2025 at 03:10 UTC** rerun uses the updated Codex bootstrap
to install Go Task in `.venv/bin` and the repaired Taskfile targets, so
`uv run task verify` now reaches `flake8` before failing on the existing style
regressions while `uv run task coverage` completes the extras sync before
failing in the scout gate regression test (see
[scout-gate-test][scout-gate-test]).
The new evidence lives at
`baseline/logs/task-verify-20250928T031021Z.log` and
`baseline/logs/task-coverage-20250928T031031Z.log`.
【F:scripts/codex_setup.sh†L1-L66】【F:Taskfile.yml†L1-L136】
【F:baseline/logs/task-verify-20250928T031021Z.log†L1-L68】
【F:baseline/logs/task-coverage-20250928T031031Z.log†L1-L120】
【F:baseline/logs/task-coverage-20250928T031031Z.log†L200-L280】

The earlier **September 28, 2025 at 01:10 UTC** attempt still records the
"Task \"verify\" does not exist" / "Task \"coverage\" does not exist" failure
from before the Taskfile repair; those logs remain archived for comparison.
【F:baseline/logs/task-verify-20250928T011001Z.log†L1-L13】
【F:baseline/logs/task-coverage-20250928T011012Z.log†L1-L13】

`uv run task verify` succeeded on **September 25, 2025 at 02:27:17 Z**
after we normalized BM25 scores, remapped parallel aggregator payloads into
claim-friendly maps, and hardened the numpy stub to generate deterministic
arrays. The log at
[baseline/logs/task-verify-20250925T022717Z.log][verify-log-pass]
shows the storage eviction, distributed executor, and VSS-enabled search
parametrisations passing in sequence, reflecting the updates in
[src/autoresearch/search/core.py][bm25-normalization],
[src/autoresearch/orchestration/parallel.py][parallel-claims],
and [tests/stubs/numpy.py][numpy-stub-deterministic].

A targeted coverage rerun at **September 25, 2025 at 23:30:24 Z** exercised the
previously blocking suites with the same fixes and recorded a clean pass in the
[targeted coverage log][targeted-coverage-log].
The focused log keeps the coverage evidence manageable while we line up the
full sweep on refreshed CI runners.

Broader integration and performance coverage remains outstanding, but the
release gate now has reproducible verification and targeted coverage evidence
for the regressions that halted the prior alpha sweep.

An AUTO reasoning mode landed with a scout-stage synthesizer pass and a gated
escalation to dialectical debate. The same change exposed `gate_policy_enabled`
and the associated thresholds/overrides through the CLI and Streamlit UI so
operators can tune debate exits without editing TOML by hand.

[verify-log-pass]:
  ../baseline/logs/task-verify-20250925T022717Z.log
[bm25-normalization]:
  ../src/autoresearch/search/core.py#L705-L760
[parallel-claims]:
  ../src/autoresearch/orchestration/parallel.py#L145-L182
[numpy-stub-deterministic]:
  ../tests/stubs/numpy.py#L12-L81
[targeted-coverage-log]:
  ../baseline/logs/task-coverage-20250925T233024Z-targeted.log

## Milestones

- **0.1.0a1** (2026-09-15, status: in progress): Alpha preview to collect
  feedback.
- **0.1.0** (2026-10-01, status: planned): Finalized packaging, docs and CI
  checks with all tests passing.
- **0.1.1** (2026-12-15, status: planned): Bug fixes and documentation
  updates (deliver-bug-fixes-and-docs-update).
- **0.2.0** (2027-03-01, status: planned): API stabilization, configuration
  hot-reload and improved search backends.
  - stabilize-api-and-improve-search
    - streaming-webhook-refinements
    - configuration-hot-reload-tests
    - hybrid-search-ranking-benchmarks
- **0.3.0** (2027-06-01, status: planned): Distributed execution support and
  monitoring utilities.
  - simulate-distributed-orchestrator-performance
- **1.0.0** (2027-09-01, status: planned): Full feature set, performance
  tuning and stable interfaces
  (reach-stable-performance-and-interfaces).

To gather early feedback, an alpha **0.1.0a1** release is targeted for
**September 15, 2026**. The final **0.1.0** milestone is set for
**October 1, 2026** while packaging tasks are resolved.

### Alpha release checklist

- [x] Confirm STATUS.md and this plan share the same coverage details before
  tagging. CI runs `scripts/update_coverage_docs.py` after `task coverage` to
  sync the value.
- [x] Ensure Task CLI available (restore-task-cli-availability).
- [x] Resolve coverage hang (fix-task-verify-coverage-hang).

These tasks completed in order: environment bootstrap → packaging verification
→ integration tests → coverage gates → algorithm validation.

### Prerequisites for tagging 0.1.0a1

Run `uv run task release:alpha` to execute the full readiness sweep before
tagging a future alpha build. The command installs the dev-minimal, test, and
default optional extras (excluding `gpu`). It then runs lint, type checks, spec
lint, the verify and coverage tasks, packaging builds, metadata checks, and the
TestPyPI dry run. Pass `EXTRAS="gpu"` when GPU wheels are staged.

- [x] Source the Task PATH helper or invoke release commands through
  `uv run task …` as described in
  [releasing.md](releasing.md#preparing-the-environment). `scripts/setup.sh`
  now refreshes `.autoresearch/path.sh` with the Task installation directory,
  so the helper exposes the CLI in new shells without manual edits.
  Reference the [STATUS.md][status-cli] log when that guidance changes.
  【F:scripts/setup.sh†L9-L93】【F:docs/releasing.md†L11-L15】

- [x] `uv run --extra dev-minimal --extra test flake8 src tests` ran as part of
  the sweep before coverage began and the log advanced to the mypy step without
  surfacing lint errors.
  【F:baseline/logs/release-alpha-20250924T184646Z.log†L1-L3】
- [x] `uv run --extra dev-minimal --extra test mypy src` reported "Success: no
  issues found in 115 source files" with the a2a interface exclusion still
  applied.
  【F:baseline/logs/release-alpha-20250924T184646Z.log†L3-L4】
- [x] `uv run python scripts/lint_specs.py` executed during the sweep to keep
  the monitor and extensions templates aligned.
  【F:baseline/logs/release-alpha-20250924T184646Z.log†L5-L5】
- [x] `uv run --extra docs mkdocs build` completed outside the sweep; the new
  log at `baseline/logs/mkdocs-build-20250925T001535Z.log` confirms the docs
  extras compile cleanly while verify remains blocked.
  【F:baseline/logs/mkdocs-build-20250925T001535Z.log†L1-L15】
- [x] `uv run task verify` completed on 2025-09-25 at 02:27:17 Z after the
  BM25 normalization, parallel aggregator payload mapping, and deterministic
  numpy stub fixes cleared the storage eviction and distributed executor
  regressions. A targeted coverage follow-up at 23:30:24 Z replayed the same
  suites to confirm the behaviour while we schedule a full sweep on refreshed
  runners.
  【F:baseline/logs/task-verify-20250925T022717Z.log†L332-L360】
  【F:baseline/logs/task-verify-20250925T022717Z.log†L400-L420】
  【F:baseline/logs/task-coverage-20250925T233024Z-targeted.log†L1-L14】
  【F:src/autoresearch/search/core.py†L705-L760】
  【F:src/autoresearch/orchestration/parallel.py†L145-L182】
  【F:tests/stubs/numpy.py†L12-L81】
- [x] Revalidated the DuckDB vector path now emits two search-phase instance
  lookups plus the direct-only pair (four calls total) while the legacy branch
  stays capped at the direct pair. The refreshed
  `tests/unit/test_core_modules_additional.py::test_search_stub_backend`
  snapshots the counts through `vector_search_counts_log`, and the reproduction
  log confirms the deterministic four-event breakdown for the vector flow.
  【F:tests/unit/test_core_modules_additional.py†L18-L379】
  【22e0d1†L1-L11】
- [x] `uv run --extra build python -m build` succeeded out of band and archived
  `baseline/logs/python-build-20250925T001554Z.log`, so packaging is ready to
  resume once verify and coverage pass.
  【F:baseline/logs/python-build-20250925T001554Z.log†L1-L14】
- [ ] Dry-run publish to TestPyPI remains on hold per the release plan until
  the verify and coverage regressions are cleared and the directive to skip the
  publish stage is lifted.
  【F:baseline/logs/release-alpha-20250929T000814Z.summary.md†L7-L10】
- [x] Archived
  [issues/archive/retire-stale-xfail-markers-in-unit-suite.md],
  [issues/archive/refresh-token-budget-monotonicity-proof.md], and
  [issues/archive/stage-0-1-0a1-release-artifacts.md] so XPASS promotions,
  heuristics proofs, and packaging logs landed together.
  【F:issues/archive/retire-stale-xfail-markers-in-unit-suite.md†L1-L81】
  【F:issues/archive/refresh-token-budget-monotonicity-proof.md†L1-L74】
  【F:issues/archive/stage-0-1-0a1-release-artifacts.md†L1-L40】
- [x] Archived
  [issues/archive/stabilize-ranking-weight-property.md],
  [issues/archive/restore-external-lookup-search-flow.md],
  [issues/archive/finalize-search-parser-backends.md], and
  [issues/archive/stabilize-storage-eviction-property.md] so the remaining
  XFAIL guards were resolved before tagging.
  【F:issues/archive/stabilize-ranking-weight-property.md†L1-L57】
  【F:issues/archive/restore-external-lookup-search-flow.md†L1-L58】
  【F:issues/archive/finalize-search-parser-backends.md†L1-L51】
  【F:issues/archive/stabilize-storage-eviction-property.md†L1-L53】

The **0.1.0a1** date is re-targeted for **September 15, 2026** and the release
remains in progress until these prerequisites are satisfied.

Completion of these items confirms the alpha baseline for **0.1.0**.

## Release Phases

1. **Planning** – finalize scope and update the roadmap.
2. **Development** – implement features and expand test coverage.
3. **Stabilization** – fix bugs, write documentation and run the full test
   suite.
4. **Publish** – follow the workflow in `deployment.md`: run
   `task bump-version -- <new-version>`, run tests, publish to TestPyPI using
   `./scripts/publish_dev.py`, then release to PyPI with `twine upload dist/*`.

Each milestone may include additional patch releases for critical fixes.

## Packaging Workflow

1. `task bump-version -- <new-version>`
2. `uv pip install build twine`
3. `uv build`
4. `uv run twine check dist/*`
5. `uv run python scripts/publish_dev.py --dry-run`
6. Set `TWINE_USERNAME` and `TWINE_PASSWORD` then run
   `uv run twine upload --repository testpypi dist/*`
7. After verifying TestPyPI, publish to PyPI with
   `uv run twine upload dist/*`.

## CI Checklist

Before tagging **0.1.0**, ensure the following checks pass. `task verify`
syncs with `--python-platform x86_64-manylinux_2_28` to prefer wheels. It
installs only `dev-minimal` and `test` extras by default; add groups with
`EXTRAS`, e.g. `EXTRAS="nlp ui"` or `EXTRAS="gpu"`:

- [ ] `uv run flake8 src tests`
- [ ] `uv run mypy src`
- [ ] `uv run pytest -q`
- [ ] `uv run pytest tests/behavior`
- [ ] `task coverage` reports **100% coverage** for targeted modules; keep docs
  in sync and stay above **90%**
- [ ] `scripts/update_coverage_docs.py` syncs docs with
  `baseline/coverage.xml`

[status-cli]:
  https://github.com/autoresearch/autoresearch/blob/main/STATUS.md#status

