# Autoresearch Roadmap

This roadmap summarizes planned features for upcoming releases.
Dates and milestones align with the [release plan](docs/release_plan.md).
See [STATUS.md](STATUS.md) and [CHANGELOG.md](CHANGELOG.md) for current results
and recent changes. Installation and environment details are covered in the
[README](README.md). Last updated **September 13, 2025**.

## Status

See [STATUS.md](STATUS.md) for current results and
[CHANGELOG.md](CHANGELOG.md) for recent updates. 0.1.0a1 remains untagged and
targets **September 15, 2026**, with **0.1.0** planned for **October 1, 2026**
across project documentation. The `task` command is currently unavailable and
`uv run pytest` reports 43 failing integration tests covering API authentication,
ranking, and storage. Reopened
[fix-api-authentication-and-metrics-tests](issues/fix-api-authentication-and-metrics-tests.md),
[fix-search-ranking-and-extension-tests](issues/fix-search-ranking-and-extension-tests.md),
and
[fix-storage-integration-test-failures](issues/fix-storage-integration-test-failures.md)
track these regressions. Once `task` is restored, `task verify` still exits with
a multiprocessing resource tracker `KeyError` after unit tests.
Scheduler resource benchmarks
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
  - [stabilize-api-and-improve-search](
    issues/archive/stabilize-api-and-improve-search.md)
    - [streaming-webhook-refinements](
      issues/archive/streaming-webhook-refinements.md)
    - [configuration-hot-reload-tests](
      issues/archive/configuration-hot-reload-tests.md)
    - [hybrid-search-ranking-benchmarks](
      issues/archive/hybrid-search-ranking-benchmarks.md)
- 0.3.0 (2027-06-01, status: planned): Distributed execution support and
  monitoring utilities.
  - [simulate-distributed-orchestrator-performance](
    issues/archive/simulate-distributed-orchestrator-performance.md)
- 1.0.0 (2027-09-01, status: planned): Full feature set, performance tuning
  and stable interfaces.
    - [reach-stable-performance-and-interfaces](
      issues/archive/reach-stable-performance-and-interfaces.md)
    - [containerize-and-package](issues/archive/containerize-and-package.md) (2026-12-01)
    - [validate-deployment-configurations](issues/archive/validate-deployment-configurations.md)
      (2027-04-15, depends on containerization)
    - [tune-system-performance](issues/archive/tune-system-performance.md)
      (2027-07-01, depends on deployment validation)

See [docs/release_plan.md](docs/release_plan.md#alpha-release-checklist)
for the alpha release checklist.

## 0.1.0a1 – Alpha preview

This pre-release will provide an early package for testing once packaging tasks
are verified. Related issue
([prepare-first-alpha-release](issues/prepare-first-alpha-release.md)) tracks
the work. Tagging **0.1.0a1** requires `task verify` to run to completion,
coverage to reach **90%** once tests run, and a successful TestPyPI upload. The
release is re-targeted for **September 15, 2026**. Key activities include:

- [x] Environment bootstrap documented and installation instructions
  consolidated.
- [ ] Task CLI availability restored
  ([install-task-cli-system-level](issues/install-task-cli-system-level.md)).
- [x] Packaging verification with DuckDB fallback.
- [x] Improve DuckDB extension fallback
  ([improve-duckdb-extension-fallback](issues/archive/improve-duckdb-extension-fallback.md)).
- [ ] Integration tests stabilized
  ([fix-api-authentication-and-metrics-tests](issues/fix-api-authentication-and-metrics-tests.md),
  [fix-search-ranking-and-extension-tests](issues/fix-search-ranking-and-extension-tests.md),
  [fix-storage-integration-test-failures](issues/fix-storage-integration-test-failures.md)).
- [ ] Coverage gates target **90%** total coverage once tests run
  ([add-test-coverage-for-optional-components](
  issues/archive/add-test-coverage-for-optional-components.md);
  [fix-task-verify-coverage-hang](
  issues/archive/fix-task-verify-coverage-hang.md)).
- [x] Algorithm validation for ranking and coordination
  ([add-ranking-algorithm-proofs-and-simulations](
  issues/archive/add-ranking-algorithm-proofs-and-simulations.md)).

These steps proceed in sequence: environment bootstrap → packaging
verification → integration tests → coverage gates → algorithm validation.

[fix-task-check-deps]: issues/archive/fix-task-check-dependency-removal-and-extension-bootstrap.md

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

- [containerize-and-package](issues/archive/containerize-and-package.md) (2026-12-01)
- [validate-deployment-configurations](issues/archive/validate-deployment-configurations.md)
  (2027-04-15, depends on containerization)
- [tune-system-performance](issues/archive/tune-system-performance.md)
  (2027-07-01, depends on deployment validation)

These tasks proceed sequentially: containerization → deployment validation → performance tuning.

