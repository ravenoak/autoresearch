# Changelog

All notable changes to this project will be documented in this file.

Reference issues by slugged filename (for example,
`issues/archive/example-issue.md`) and avoid numeric prefixes.

## [Unreleased]
- Prevented overweight search ranking vectors from being silently normalised by
  raising a `ConfigError` and documenting the behaviour in
  [docs/specs/config.md](docs/specs/config.md).
- Logged the config weight validation regression in
  [fix-config-weight-sum-validation](issues/fix-config-weight-sum-validation.md).
- Captured offline DuckDB extension fallback failures in
  [fix-duckdb-extension-offline-fallback](issues/fix-duckdb-extension-offline-fallback.md).
- Narrowed the search regression scope in
  [fix-search-ranking-and-extension-tests](issues/fix-search-ranking-and-extension-tests.md),
  which now focuses on the VSS loader mock expectations.
- Continued to track documentation build warnings in
  [fix-mkdocs-griffe-warnings](issues/fix-mkdocs-griffe-warnings.md).

## [0.1.0a1] - Unreleased
- Local-first orchestrator coordinating multiple agents for research
  workflows.
- CLI, HTTP API, and Streamlit interfaces for executing queries.
- Hybrid DuckDB and RDF knowledge graph with plugin-based search backends.
- Prometheus metrics, interactive mode, and graph visualization utilities.
- Release remains pending while tests, coverage, and documentation builds are
  stabilized (see the issues referenced above and in [STATUS.md](STATUS.md)).

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


