# Changelog

All notable changes to this project will be documented in this file.

Reference issues by slugged filename (for example,
`issues/archive/example-issue.md`) and avoid numeric prefixes.

## [Unreleased]

- Documented research federation requirements F-28–F-31, updated the RTM, and
  aligned roadmap, CLI, and desktop guides with the staged specification.
- Added an opt-in guard for the legacy Streamlit GUI. The CLI now requires the
  `AUTORESEARCH_ENABLE_STREAMLIT` environment variable and emits migration
  guidance pointing teams to the PySide6 desktop interface.
- Introduced scholarly connectors with shared caching: arXiv and Hugging Face
  fetchers feed into `ScholarlyCache`, `StorageManager` persists metadata to
  DuckDB, and new CLI/UI actions make cached papers available to workspaces.

## [0.1.0] - 2025-11-15

**PREPARATION IN PROGRESS** - Final release engineering for stable v0.1.0 release.

### Overview
- Multi-agent orchestration with dialectical reasoning
- Local-first architecture with DuckDB and Kuzu
- CLI, HTTP API, and Streamlit interfaces
- Plugin-based search backends
- Knowledge graph integration
- Comprehensive test coverage (64% measured October 22, 2025)

### Key Features
- **Multi-Agent Orchestration**: Dialectical reasoning with contrarian, fact-checking, and summarization agents
- **Local-First Architecture**: DuckDB and Kuzu databases for privacy-preserving research
- **Flexible Query Modes**: Direct, dialectical, and chain-of-thought reasoning strategies
- **Plugin-Based Search**: File, Git, and web search backends with caching and ranking
- **Knowledge Graph Integration**: Automatic entity extraction and relationship inference
- **Circuit Breaker Protection**: Robust error handling and recovery mechanisms
- **Real-time Monitoring**: Prometheus metrics and structured logging

### Technical Quality
- **Type Safety**: Full mypy strict mode compliance across core modules (measured October 22, 2025)
- **Code Quality**: Zero linting violations, 64% test coverage (measured October 22, 2025)
- **Build Process**: Clean packaging with sdist and wheel generation
- **Testing**: 1,769 tests collected (measured October 22, 2025): unit, integration, and behavior tests
- Integration test deselection: 28% (145/513 tests) - acceptable for v0.1.0, target <15% for v0.1.1

### What's Changed Since v0.1.0a1
- Fixed authentication middleware for independent bearer token and API key authentication
- Updated documentation for accuracy and completeness with empirical data
- Verified all optional extras functionality
- Published to PyPI for easy installation
- Improved error handling and test stability (xfail count reduced from 127 to 35)
- Comprehensive coverage measurement (21,943 lines vs 57 lines previously)

### Known Limitations
- Streamlit UI components have lower test coverage (planned for v0.1.1)
- Performance is 86% of targets (optimization planned for v0.2.0)
- Some optional features require additional extras
- Integration test suite shows 2.2% failure rate when run as complete suite (tests pass individually, may be test isolation issue)

## [0.1.0a1] - 2025-10-16

Initial alpha release of the autoresearch framework featuring multi-agent research orchestration, local-first architecture, and comprehensive APIs.

### Overview
- Local-first orchestrator coordinating multiple agents for research
  workflows.
- CLI, HTTP API, and Streamlit interfaces for executing queries.
- Hybrid DuckDB and RDF knowledge graph with plugin-based search backends.
- Prometheus metrics, interactive mode, and graph visualization utilities.
- Comprehensive test suite with 1,769 tests collected (measured October 22, 2025): unit, integration, and behavior tests.

### Key Features
- **Multi-Agent Orchestration**: Dialectical reasoning with contrarian, fact-checking, and summarization agents
- **Local-First Architecture**: DuckDB and Kuzu databases for privacy-preserving research
- **Flexible Query Modes**: Direct, dialectical, and chain-of-thought reasoning strategies
- **Plugin-Based Search**: File, Git, and web search backends with caching and ranking
- **Knowledge Graph Integration**: Automatic entity extraction and relationship inference
- **Circuit Breaker Protection**: Robust error handling and recovery mechanisms
- **Real-time Monitoring**: Prometheus metrics and structured logging

### Technical Quality
- **Type Safety**: Full mypy strict mode compliance across core modules (measured October 22, 2025)
- **Code Quality**: Zero linting violations, 64% test coverage (measured October 22, 2025)
- **Build Process**: Clean packaging with sdist and wheel generation
- **Testing**: 1,769 tests collected (measured October 22, 2025), comprehensive integration coverage

### Known Limitations
- Integration tests require external service mocking for CI environments
- Optional extras (NLP, UI, GPU) testing deferred to v0.1.0 release
- Some xfailed tests remain for deprecated schema compatibility

## [Unreleased]

### Highlights
- Landed the verification loop enhancements so claim extraction telemetry feeds retry
  counters, persistence metrics, and behavior coverage while keeping audit badges visible
  during reverification sweeps.【F:src/autoresearch/orchestration/reverify.py†L73-L197】【F:tests/unit/orchestration/test_reverify.py†L1-L80】【F:tests/behavior/features/reasoning_modes.feature†L8-L22】
- Exported contradiction-aware GraphML and JSON session graphs, wiring the planner and
  gate through `SearchContext` and `QueryState` so availability and serialization flags
  persist with regression coverage.【F:src/autoresearch/knowledge/graph.py†L113-L204】【F:src/autoresearch/search/context.py†L618-L666】【F:src/autoresearch/orchestration/state.py†L1120-L1135】【F:tests/unit/storage/test_knowledge_graph.py†L1-L63】
- Repaired QueryState registry cloning, reinstated search fallback guards, and captured
  green coverage plus strict-typing sweeps to document release readiness for the
  gate.【F:src/autoresearch/orchestration/state_registry.py†L18-L148】【F:tests/unit/orchestration/test_state_registry.py†L21-L138】【F:baseline/logs/task-coverage-20250930T181947Z.log†L1-L21】【F:src/autoresearch/search/core.py†L147-L199】【F:tests/unit/search/test_query_expansion_convergence.py†L154-L206】【F:baseline/logs/mypy-strict-20251001T143959Z.log†L2358-L2377】
- Documented the final-answer audit loop, operator acknowledgement controls, and release
  governance updates across the upgrade plan, release plan, roadmap, specification,
  pseudocode, and aligned verify/coverage transcripts.【F:docs/deep_research_upgrade_plan.md†L19-L41】【F:docs/release_plan.md†L11-L24】【F:ROADMAP.md†L33-L60】【F:STATUS.md†L21-L65】【F:TASK_PROGRESS.md†L1-L18】【F:docs/specification.md†L60-L83】【F:docs/pseudocode.md†L78-L119】【F:baseline/logs/task-verify-20250930T142820Z.log†L1-L36】【F:baseline/logs/task-coverage-20250930T143024Z.log†L1-L41】
- Added AUTO-mode scout sampling and agreement gating controls alongside expanded
  Streamlit typing shims so heuristics telemetry and the UI stack stay covered without
  new runtime dependencies.【F:src/autoresearch/config/models.py†L638-L668】【F:src/autoresearch/orchestration/orchestrator.py†L353-L360】【F:tests/unit/orchestration/test_auto_mode.py†L125-L250】【F:tests/unit/orchestration/test_gate_policy.py†L178-L226】【F:docs/specs/orchestration.md†L51-L55】【F:src/autoresearch/streamlit_ui.py†L1-L120】
- Refreshed release readiness documentation and archival logs so the alpha sweep,
  verify, coverage, and build artefacts remain auditable for tag approval.【F:scripts/setup.sh†L9-L93】【F:docs/releasing.md†L11-L15】【F:docs/release_plan.md†L18-L48】【F:baseline/logs/task-verify-20250930T174512Z.log†L1-L23】【F:baseline/logs/task-coverage-20250930T181947Z.log†L1-L21】【F:baseline/logs/python-build-20250929T030953Z.log†L1-L13】

## [0.1.0a1] - 2025-10-16

Initial alpha release of the autoresearch framework featuring multi-agent research orchestration, local-first architecture, and comprehensive APIs.

### Overview
- Local-first orchestrator coordinating multiple agents for research
  workflows.
- CLI, HTTP API, and Streamlit interfaces for executing queries.
- Hybrid DuckDB and RDF knowledge graph with plugin-based search backends.
- Prometheus metrics, interactive mode, and graph visualization utilities.
- Comprehensive test suite with 1,769 tests collected (measured October 22, 2025): unit, integration, and behavior tests.

### Key Features
- **Multi-Agent Orchestration**: Dialectical reasoning with contrarian, fact-checking, and summarization agents
- **Local-First Architecture**: DuckDB and Kuzu databases for privacy-preserving research
- **Flexible Query Modes**: Direct, dialectical, and chain-of-thought reasoning strategies
- **Plugin-Based Search**: File, Git, and web search backends with caching and ranking
- **Knowledge Graph Integration**: Automatic entity extraction and relationship inference
- **Circuit Breaker Protection**: Robust error handling and recovery mechanisms
- **Real-time Monitoring**: Prometheus metrics and structured logging

### Technical Quality
- **Type Safety**: Full mypy strict mode compliance across core modules (measured October 22, 2025)
- **Code Quality**: Zero linting violations, 64% test coverage (measured October 22, 2025)
- **Build Process**: Clean packaging with sdist and wheel generation
- **Testing**: 1,769 tests collected (measured October 22, 2025), comprehensive integration coverage

### Known Limitations
- Integration tests require external service mocking for CI environments
- Optional extras (NLP, UI, GPU) testing deferred to v0.1.0 release
- Some xfailed tests remain for deprecated schema compatibility

### Testing Summary
- **Unit Tests**: 1276 passed (67 skipped, 13 xfailed for schema compatibility)
- **Integration Tests**: Core functionality tested with mocked external services
- **Behavior Tests**: 41 end-to-end workflows verified
- **Code Quality**: Zero linting errors, full type checking compliance
- **Build Process**: Successful packaging and installation verification

[add-test-coverage]: issues/archive/add-test-coverage-for-optional-components.md
[streamline-extras]: issues/archive/streamline-task-verify-extras.md

## [0.1.0] - Unreleased
Planned first public release bringing the core research workflow to life.

### Highlights
- CLI, HTTP API and Streamlit interfaces for local-first research.
- Dialectical orchestrator coordinating multiple agents with hot-reloadable
  configuration.
- Hybrid DuckDB/RDF knowledge graph persistence and plugin-based search backends
  (files, Git and web).
- Prometheus metrics, interactive mode and graph visualization utilities.

### Improvements
- Refined token budget heuristics and asynchronous cancellation handling.
- Cleaned up CLI commands and installer scripts.
- Numerous bug fixes and reliability tweaks since the initial prototype was
  created in May 2025.
  - Exposed token usage capture helper on the orchestrator for easier testing.

See the [release plan](docs/release_plan.md) for upcoming milestones.


