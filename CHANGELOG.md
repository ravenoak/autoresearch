# Changelog

All notable changes to this project will be documented in this file.

Reference issues by slugged filename (for example,
`issues/archive/example-issue.md`) and avoid numeric prefixes.

## [Unreleased]
- Documented ranking formula test failure in
  [fix-search-ranking-and-extension-tests](issues/archive/fix-search-ranking-and-extension-tests.md).
- Hardened storage concurrency and eviction logic with re-entrant locks
  guarding NetworkX writes and added
  `initialize_schema_version_without_fetchone` helper to support DuckDB
  connections lacking `fetchone`.
- Fallback to in-memory RDF store when persistent backends cannot acquire a
  file lock, ensuring concurrent storage operations succeed.

## [0.1.0a1] - Unreleased
- Local-first orchestrator coordinating multiple agents for research
  workflows.
- CLI, HTTP API, and Streamlit interfaces for executing queries.
- Hybrid DuckDB and RDF knowledge graph with plugin-based search backends.
- Prometheus metrics, interactive mode, and graph visualization utilities.
- `flake8` and `mypy` pass; unit coverage reaches 100% with `task verify`
  passing.
- Aligned FastAPI (>=0.115.12) and SlowAPI (0.1.9) pins across project files.
- Closed issues:
  - [prepare-v0-1-0a1-release](issues/archive/prepare-v0-1-0a1-release.md)
    finalizing docs, tests, and packaging.
  - [resolve-current-test-failures](issues/archive/resolve-current-test-failures.md)
    ensuring at least 90% coverage.
  - [restore-task-cli-availability](issues/archive/restore-task-cli-availability.md)
    updating release docs with Go Task 3.44.1.
  - [add-test-coverage-for-optional-components][add-test-coverage]
    expanding unit coverage.
  - [streamline-task-verify-extras][streamline-extras]
    reducing GPU downloads.
- See [release notes](docs/release_notes/v0.1.0a1.md) for details.

[add-test-coverage]: issues/archive/add-test-coverage-for-optional-components.md
[streamline-extras]: issues/archive/streamline-task-verify-extras.md

## [0.1.0] - Unreleased
Planned first public release bringing the core research workflow to life.

### Highlights
- CLI, HTTP API and Streamlit interfaces for local-first research.
- Dialectical orchestrator coordinating multiple agents with hot-reloadable configuration.
- Hybrid DuckDB/RDF knowledge graph persistence and plugin-based search backends
  (files, Git and web).
- Prometheus metrics, interactive mode and graph visualization utilities.

### Improvements
- Refined token budget heuristics and asynchronous cancellation handling.
- Cleaned up CLI commands and installer scripts.
- Numerous bug fixes and reliability tweaks since the initial prototype was created in May 2025.
  - Exposed token usage capture helper on the orchestrator for easier testing.

See the [release plan](docs/release_plan.md) for upcoming milestones.


