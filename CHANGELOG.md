# Changelog

All notable changes to this project will be documented in this file.

Reference issues by slugged filename (for example,
`issues/archive/example-issue.md`) and avoid numeric prefixes.

## [Unreleased]
- Update release plan to align milestones with the 2025 development timeline.
  - Add rich configuration context fixtures with sample data for tests. [create-more-comprehensive-test-contexts](issues/archive/create-more-comprehensive-test-contexts.md)
- Optimize mypy configuration to skip site packages, preventing hangs during
verification. [investigate-mypy-hang](issues/archive/investigate-mypy-hang.md).
- Document virtual environment best practices in the developer guide.

## [0.1.0-alpha.1] - 2025-08-09
- Verified source and wheel builds succeed; TestPyPI upload failed with 403 Forbidden.

## [0.1.0] - Unreleased
Planned first public release bringing the core research workflow to life.

### Highlights
- CLI, HTTP API and Streamlit interfaces for local-first research.
- Dialectical orchestrator coordinating multiple agents with hot-reloadable configuration.
- Hybrid DuckDB/RDF knowledge graph persistence and plugin-based search backends (files, Git and web).
- Prometheus metrics, interactive mode and graph visualization utilities.

### Improvements
- Refined token budget heuristics and asynchronous cancellation handling.
- Cleaned up CLI commands and installer scripts.
- Numerous bug fixes and reliability tweaks since the initial prototype was created in May 2025.

See the [release plan](docs/release_plan.md) for upcoming milestones.

