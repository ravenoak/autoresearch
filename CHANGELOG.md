# Changelog

All notable changes to this project will be documented in this file.

Reference issues by slugged filename (for example,
`issues/archive/example-issue.md`) and avoid numeric prefixes.

## [Unreleased]
- `v0.1.0a1` remains untagged; the alpha targets **September 15, 2026** and
  0.1.0 aims for **October 1, 2026**. See [STATUS.md](STATUS.md),
  [docs/release_plan.md](docs/release_plan.md), and
  [ROADMAP.md](ROADMAP.md) for aligned milestones.
- Track environment alignment to ensure Python 3.12 and dev tooling are
  available.
    [align-environment-with-requirements]
- Record current test suite status as of 2025-09-10: all 844 tests passing
  (34 skipped, 25 deselected, 7 xfailed, 5 xpassed) with **95%** coverage
  (57/57 lines).
    [resolve-current-integration-test-failures]
    [resolve-pre-alpha-release-blockers]
- Update release plan with revised milestone schedule; 0.1.0a1 marked in
  progress and coverage noted at **95%**.
- Summarize blockers before tagging 0.1.0a1 (`check_env` warnings and TestPyPI
  403) with **95%** coverage achieved.
  - Add rich configuration context fixtures with sample data for tests.
    [create-more-comprehensive-test-contexts]
- Optimize mypy configuration to skip site packages, preventing hangs during
verification. [investigate-mypy-hang](issues/archive/investigate-mypy-hang.md).
- Document virtual environment best practices in the developer guide.
 - Synchronize release documentation across project files.
    [update-release-documentation]
- Fix BM25 search scoring method signature.
- Correct search backend registration and reset logic.
- Pin Python version and expand setup checks to prevent environment drift.
    [align-environment-with-requirements]
- Enable Pydantic plugin for static type analysis.
- Harden storage against concurrency and initialization edge cases.
- Record storage module coverage at ~50% from integration tests.
- Document final release workflow and TestPyPI publishing steps.
- Clarified directory scopes and noted missing instructions for `src/`, `scripts/`, and `examples/`.
- Drafted preliminary release notes and validated README installation steps.
  [assemble-release-notes-readme]
- Handle DuckDB API changes by using `fetchall` for schema version lookup to
  prevent `AttributeError` during table creation.

### 0.1.0a1 – Unreleased (target 2026-09-15)
- Documented offline DuckDB VSS extension fallback and referenced its
  integration test.
- Added minimal install steps for the `llm` extra.
- Performed TestPyPI publish dry run.
- See [release notes](docs/release_notes/v0.1.0a1.md) for features and gaps.

### Preliminary release notes
- Aligned FastAPI (>=0.115.12) and SlowAPI (0.1.9) pins across project files.
- Updated release plan to reflect installed test dependencies and active blockers.

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

[align-environment-with-requirements]: issues/archive/align-environment-with-requirements.md
[create-more-comprehensive-test-contexts]: issues/archive/create-more-comprehensive-test-contexts.md
[update-release-documentation]: issues/archive/update-release-documentation.md
[assemble-release-notes-readme]: issues/archive/assemble-release-notes-and-validate-readme.md
[resolve-current-integration-test-failures]: issues/resolve-current-integration-test-failures.md
[resolve-pre-alpha-release-blockers]: issues/archive/resolve-pre-alpha-release-blockers.md

