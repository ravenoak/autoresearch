# Autoresearch Roadmap

This roadmap summarizes planned features for upcoming releases.
Dates and milestones align with the [release plan](docs/release_plan.md).
See [STATUS.md](STATUS.md) and [CHANGELOG.md](CHANGELOG.md) for current results
and recent changes. Installation and environment details are covered in the
[README](README.md). Last updated **September 17, 2025**.

## Status

See [STATUS.md](STATUS.md) for current results and
[CHANGELOG.md](CHANGELOG.md) for recent updates. 0.1.0a1 remains untagged and
targets **September 15, 2026**, with **0.1.0** planned for **October 1, 2026**
across project documentation. The evaluation container still lacks the Go Task
CLI on first boot, so `uv run task check` fails until `scripts/setup.sh` or a
manual install provides the binary. Running `uv sync --extra dev-minimal --extra
test` followed by `uv run python scripts/check_env.py` leaves only the missing
Go Task CLI warning in this environment. 【024fb5†L1-L13】【f56f62†L1-L24】
Targeted tests on **September 17, 2025** show the DuckDB extension loader suite
and `tests/unit/search/test_ranking_formula.py::`
`test_rank_results_weighted_combination` now pass with the documented convex
weights. 【af6378†L1-L2】【75e1fd†L1-L2】 However, `uv run --extra test pytest`
`tests/unit -q` fails during collection because
`scripts/distributed_coordination_sim.py` no longer exports `elect_leader` or
`process_messages`, so the distributed property tests cannot import their
reference helpers. 【b4944c†L1-L23】 Integration scenarios for ranking
consistency and optional extras still pass with the `[test]` extras installed,
and CLI helper plus data analysis suites run with
`PYTHONWARNINGS=error::DeprecationWarning` without warnings.
【50b44e†L1-L2】【7a8f55†L1-L2】
`uv run mkdocs build` still fails until docs extras install `mkdocs`.
【6bcbaa†L1-L3】 Release blockers remain
in [restore-distributed-coordination-simulation-exports](
issues/restore-distributed-coordination-simulation-exports.md),
[resolve-resource-tracker-errors-in-verify](
issues/resolve-resource-tracker-errors-in-verify.md),
[resolve-deprecation-warnings-in-tests](
issues/resolve-deprecation-warnings-in-tests.md), and
[prepare-first-alpha-release](issues/prepare-first-alpha-release.md).
Specification updates for the API, CLI helpers, config, distributed execution,
extensions, and monitor packages were reviewed and archived after confirming
the docs match the implementation. Scheduler resource benchmarks
(`scripts/scheduling_resource_benchmark.py`) offer utilization and memory
estimates documented in `docs/orchestrator_perf.md`. Dependency pins:
`fastapi>=0.115.12` and `slowapi==0.1.9`. Use Python 3.12+ with:

```
uv venv && uv sync --all-extras &&
uv pip install -e '.[full,parsers,git,llm,dev]'
```

before running tests.

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
    - [restore-distributed-coordination-simulation-exports]
    - [resolve-resource-tracker-errors-in-verify]
    - [resolve-deprecation-warnings-in-tests]

See [docs/release_plan.md](docs/release_plan.md#alpha-release-checklist)
for the alpha release checklist.

[prepare-first-alpha-release]: issues/prepare-first-alpha-release.md
[restore-distributed-coordination-simulation-exports]:
  issues/restore-distributed-coordination-simulation-exports.md
[resolve-resource-tracker-errors-in-verify]:
  issues/resolve-resource-tracker-errors-in-verify.md
[resolve-deprecation-warnings-in-tests]:
  issues/resolve-deprecation-warnings-in-tests.md

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
- [ ] Distributed coordination helpers restored
  ([restore-distributed-coordination-simulation-exports]).
- [ ] `task verify` completes without resource tracker errors
  ([resolve-resource-tracker-errors-in-verify]).
- [ ] Deprecation warnings removed from test runs
  ([resolve-deprecation-warnings-in-tests]).
- [ ] Coverage and release packaging finalized for the alpha tag
  ([prepare-first-alpha-release]).
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
  [restore-distributed-coordination-simulation-exports],
  [resolve-resource-tracker-errors-in-verify], and
  [resolve-deprecation-warnings-in-tests].
- Long-term operations rely on keeping the distributed and monitor
  specifications in sync with implementation changes; both docs were reviewed
  on September 17, 2025.

These tasks proceed sequentially: containerization → deployment validation →
performance tuning.

