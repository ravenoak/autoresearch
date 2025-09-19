# Autoresearch Roadmap

This roadmap summarizes planned features for upcoming releases.
Dates and milestones align with the [release plan](docs/release_plan.md).
See [STATUS.md](STATUS.md) and [CHANGELOG.md](CHANGELOG.md) for current results
and recent changes. Installation and environment details are covered in the
[README](README.md). Last updated **September 19, 2025**.

## Status

See [STATUS.md](STATUS.md) for detailed logs and
[CHANGELOG.md](CHANGELOG.md) for recent updates. 0.1.0a1 remains untagged and
targets **September 15, 2026**, with **0.1.0** planned for **October 1, 2026**
across project documentation. Loading the PATH helper emitted by
`./scripts/setup.sh --print-path` makes `task --version` report 3.45.4 in the
base shell, and `uv run python scripts/check_env.py` confirms the expected
toolchain whenever the `dev-minimal` and `test` extras are synced.
【5d8a01†L1-L2】【0feb5e†L1-L17】【fa650a†L1-L10】 Storage regressions are contained:
`uv run --extra test pytest tests/unit -k "storage" -q --maxfail=1` reports 135
passed, 2 skipped, 1 xfailed, and 1 xpassed tests. 【dbf750†L1-L1】 The lone xpass
comes from `tests/unit/test_storage_errors.py::test_setup_rdf_store_error`,
which still succeeds despite the stale xfail marker. 【cd543d†L1-L1】
`uv run python scripts/lint_specs.py` fails because `docs/specs/monitor.md` and
`docs/specs/extensions.md` drifted from the spec template, and
`issues/restore-spec-lint-template-compliance.md` tracks the fix so linting can
reach tests again. 【4076c9†L1-L2】【F:issues/restore-spec-lint-template-compliance.md†L1-L33】
`uv run --extra docs mkdocs build` succeeds without navigation warnings,
confirming the documentation pipeline stays green. 【e808c5†L1-L2】 Release
blockers therefore include restoring spec lint compliance, running
`task verify` without resource tracker errors, sweeping for deprecation warnings
with `PYTHONWARNINGS=error::DeprecationWarning`, refreshing coverage, and then
closing the alpha-release checklist.【F:issues/restore-spec-lint-template-compliance.md†L1-L33】【F:issues/resolve-resource-tracker-errors-in-verify.md†L1-L33】【F:issues/resolve-deprecation-warnings-in-tests.md†L1-L39】【F:issues/rerun-task-coverage-after-storage-fix.md†L1-L33】

## Milestones

- 0.1.0a1 (2026-09-15, status: in progress): Alpha preview to collect
  feedback while aligning environment requirements.
- 0.1.0 (2026-10-01, status: planned): Finalized packaging, docs and CI
  checks with all tests passing.
- 0.1.1 (2026-12-15, status: planned): Bug fixes and documentation updates.
- 0.2.0 (2027-03-01, status: planned): API stabilization, configuration
  hot-reload and improved search backends.
- 0.3.0 (2027-06-01, status: planned): Distributed execution support and
  monitoring utilities.
  - 1.0.0 (2027-09-01, status: planned): Full feature set, performance tuning
    and stable interfaces.
  - Stability goals depend on closing:
    - [prepare-first-alpha-release]
    - [resolve-resource-tracker-errors-in-verify]
    - [resolve-deprecation-warnings-in-tests]
    - [restore-spec-lint-template-compliance]

See [docs/release_plan.md](docs/release_plan.md#alpha-release-checklist)
for the alpha release checklist.

[prepare-first-alpha-release]: issues/prepare-first-alpha-release.md
[resolve-resource-tracker-errors-in-verify]:
  issues/resolve-resource-tracker-errors-in-verify.md
[resolve-deprecation-warnings-in-tests]:
  issues/resolve-deprecation-warnings-in-tests.md
[restore-spec-lint-template-compliance]:
  issues/restore-spec-lint-template-compliance.md

## 0.1.0a1 – Alpha preview

This pre-release will provide an early package for testing once packaging tasks
are verified. Related issue
([prepare-first-alpha-release](issues/prepare-first-alpha-release.md)) tracks
the work. Tagging **0.1.0a1** requires `task verify` to run to completion,
coverage to reach **90%** once tests run, and a successful TestPyPI upload. The
release is re-targeted for **September 15, 2026**. Key activities include:

- [x] Environment bootstrap documented and installation instructions
  consolidated.
- [x] Task CLI availability restored.
- [x] Packaging verification with DuckDB fallback.
- [x] DuckDB extension fallback hardened for offline setups.
- [x] Distributed coordination helpers restored
  ([issues/archive/restore-distributed-coordination-simulation-exports.md](issues/archive/restore-distributed-coordination-simulation-exports.md)).
- [ ] `task verify` completes without resource tracker errors
  ([resolve-resource-tracker-errors-in-verify]).
- [ ] Deprecation warnings removed from test runs
  ([resolve-deprecation-warnings-in-tests]).
- [ ] Coverage and release packaging finalized for the alpha tag
  ([prepare-first-alpha-release]).
- [ ] Storage setup concurrency crash resolved
  ([address-storage-setup-concurrency-crash]).
- [x] Algorithm validation for ranking and coordination.
- [x] Formal validation for the OxiGraph backend.

These steps proceed in sequence: environment bootstrap → packaging
verification → integration tests → coverage gates → algorithm validation.

## 0.1.0 – First public preview

The final 0.1.0 release focuses on making the project installable and
providing complete documentation once the open issues are resolved. Key
activities include:

- Running all unit, integration and behavior tests (see [STATUS.md](STATUS.md)).
- Finalizing API reference and user guides.
- Verifying packaging metadata and TestPyPI uploads.
- Document domain model for agents, queries, storage, and search.

Type checking and unit tests currently fail; see [STATUS.md](STATUS.md) for
details. The **0.1.0** milestone is targeted for **October 1, 2026** while
packaging tasks are resolved.

## 0.1.1 – Bug fixes and documentation updates

Before publishing 0.1.0 the release plan lists several checks:

- Verify all automated tests pass in CI.
- Review documentation for clarity using a Socratic approach.
- Conduct a dialectical evaluation of core workflows.
- Ensure packaging metadata and publish scripts work correctly.

Any remaining issues from these tasks will be addressed in 0.1.1.

- CLI backup commands and testing utilities remain pending, while specialized
  agents—Moderator, Specialist, and User—are already implemented
  (`src/autoresearch/agents/specialized/moderator.py`,
  `src/autoresearch/agents/specialized/domain_specialist.py`,
  `src/autoresearch/agents/specialized/user_agent.py`) and will receive
  comprehensive unit tests once testing passes. The 0.1.1 release is planned for
  **December 15, 2026**.

## 0.2.0 – API stabilization and improved search

The next minor release focuses on API improvements and search enhancements:

- Complete all search backends with cross-backend ranking and
  embedding-based search (see tasks in CODE_COMPLETE_PLAN lines 38-46).
- Add streaming responses and webhook notifications to the REST API
  (implemented per TASK_PROGRESS lines 143-150).
- Support hybrid keyword/semantic search and a unified ranking algorithm.
- Continue refining the web interface and visualization tools.

## 0.3.0 – Distributed execution and monitoring

Key features planned for this release include:

- Distributed agent execution across processes and storage backends
  (see CODE_COMPLETE_PLAN lines 156-160 and TASK_PROGRESS lines 182-192).
- Coordination mechanisms for distributed agents and parallel search.
- Expanded monitoring including real-time metrics and GPU usage.

## 1.0.0 – Stable interfaces and performance tuning

The 1.0.0 milestone aims for a polished, production-ready system:

- Packaging and deployment planning draw on [prepare-first-alpha-release].
- Integration stability depends on closing
  [address-storage-setup-concurrency-crash],
  [resolve-resource-tracker-errors-in-verify], and
  [resolve-deprecation-warnings-in-tests].
- Long-term operations rely on keeping the distributed and monitor
  specifications in sync with implementation changes; both docs were reviewed
  on September 17, 2025.

These tasks proceed sequentially: containerization → deployment validation →
performance tuning.

