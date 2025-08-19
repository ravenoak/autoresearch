# Changelog

All notable changes to this project will be documented in this file.

Reference issues by slugged filename (for example,
`issues/archive/example-issue.md`) and avoid numeric prefixes.

## [Unreleased]
- Track environment alignment to ensure Python 3.12 and dev tooling are
  available.
    [align-environment-with-requirements]
 - Update release plan with revised milestone schedule.
  - Add rich configuration context fixtures with sample data for tests.
    [create-more-comprehensive-test-contexts]
- Optimize mypy configuration to skip site packages, preventing hangs during
verification. [investigate-mypy-hang](issues/archive/investigate-mypy-hang.md).
- Document virtual environment best practices in the developer guide.
 - Synchronize release documentation across project files.
    [update-release-documentation]
 - Fix BM25 search scoring method signature.
    [resolve-current-test-failures]
 - Correct search backend registration and reset logic.
    [resolve-current-test-failures]
 - Pin Python version and expand setup checks to prevent environment drift.
    [align-environment-with-requirements]
 - Enable Pydantic plugin for static type analysis.
    [resolve-current-test-failures]
- Document final release workflow and TestPyPI publishing steps.
- Clarified directory scopes and noted missing instructions for `src/`, `scripts/`, and `examples/`.

### Preliminary release notes
- Aligned FastAPI (>=0.115.12) and SlowAPI (0.1.9) pins across project files.
- Updated release plan to reflect installed test dependencies and active blockers.

## [0.1.0-alpha.1] - 2026-03-01
- Verified source and wheel builds succeed; TestPyPI upload failed with 403 Forbidden.

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
  - Exposed token usage capture helper on the orchestrator for easier testing
    ([resolve-current-test-failures]).

See the [release plan](docs/release_plan.md) for upcoming milestones.

[align-environment-with-requirements]: issues/align-environment-with-requirements.md
[create-more-comprehensive-test-contexts]: issues/archive/create-more-comprehensive-test-contexts.md
[update-release-documentation]: issues/archive/update-release-documentation.md
[resolve-current-test-failures]: issues/resolve-current-test-failures.md

