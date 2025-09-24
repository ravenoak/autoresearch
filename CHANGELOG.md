# Changelog

All notable changes to this project will be documented in this file.

Reference issues by slugged filename (for example,
`issues/archive/example-issue.md`) and avoid numeric prefixes.

## [Unreleased]
- Finalized PDF and DOCX ingestion for 0.1.0a1 by introducing a deterministic
  parser module, documenting the scope decision, and promoting parser tests
  from XFAIL to regression coverage, addressing
  [finalize-search-parser-backends](issues/finalize-search-parser-backends.md).
  【F:src/autoresearch/search/parsers.py†L1-L149】【F:src/autoresearch/search/core.py†L55-L183】
  【F:docs/algorithms/search.md†L1-L74】【F:docs/algorithms/cache.md†L1-L52】
  【F:tests/unit/test_search_parsers.py†L1-L74】
- Restored the storage-backed hybrid lookup flow by exposing
  `StorageManager` through `autoresearch.search`, rehydrating vector,
  BM25, and ontology signals during `Search.external_lookup`, and
  enabling the vector and hybrid query unit tests.
  【F:src/autoresearch/search/__init__.py†L10-L38】【F:src/autoresearch/search/core.py†L320-L382】
  【F:src/autoresearch/search/core.py†L904-L1087】【F:src/autoresearch/search/core.py†L1352-L1475】
  【F:tests/unit/test_search.py†L296-L314】【F:tests/unit/test_search.py†L404-L429】
- Stabilized storage eviction by documenting the stale-LRU counterexample,
  adding a fallback when caches are empty, extending the property-based
  regression, and introducing a `stale_lru` simulation scenario.
- Reframed the token budget spec around piecewise monotonicity,
  documented the zero-usage counterexample, and promoted deterministic
  regression coverage for
  [refresh-token-budget-monotonicity-proof](issues/refresh-token-budget-monotonicity-proof.md).
- Archived [resolve-deprecation-warnings-in-tests](issues/archive/resolve-deprecation-warnings-in-tests.md)
  after removing the repository-wide `pkg_resources` suppression from
  `sitecustomize.py` and capturing a clean `task verify:warnings:log` run at
  `baseline/logs/verify-warnings-20250923T224648Z.log`.
  【F:sitecustomize.py†L1-L37】【F:baseline/logs/verify-warnings-20250923T224648Z.log†L1047-L1047】
  【F:baseline/logs/verify-warnings-20250923T224648Z.log†L1442-L1442】
  【F:baseline/logs/verify-warnings-20250923T224648Z.log†L1749-L1749】
- Documented deterministic eviction fallback when OS metrics are unavailable
  and enforced ranking weight sums before normalization across the storage and
  search modules.
- Migrated integration tests to use `content=` with `httpx`, pinned the
  dependency to the 0.28.x series, and recorded the `content` deprecation
  warning in
  [resolve-deprecation-warnings-in-tests](issues/archive/resolve-deprecation-warnings-in-tests.md).
- Prevented overweight search ranking vectors from being silently normalised by
  raising a `ConfigError` and documenting the behaviour in
  [docs/specs/config.md](docs/specs/config.md).
- Logged the config weight validation regression in
  [fix-config-weight-sum-validation](
    issues/archive/fix-config-weight-sum-validation.md).
- Captured offline DuckDB extension fallback failures in
  [fix-duckdb-extension-offline-fallback](
    issues/archive/fix-duckdb-extension-offline-fallback.md).
- Narrowed the search regression scope in
  [fix-search-ranking-and-extension-tests](
    issues/archive/fix-search-ranking-and-extension-tests.md), which now focuses on
  aligning the overweight ranking unit test with the validator while extension
  loader suites pass.
- Continued to track documentation build warnings in
  [fix-mkdocs-griffe-warnings](issues/archive/fix-mkdocs-griffe-warnings.md).
- Replaced deprecated `fastembed.TextEmbedding` imports with the new
  `OnnxTextEmbedding` entry point, updated stubs and tests to mirror the public
  API, and noted the migration in
  [resolve-deprecation-warnings-in-tests](
    issues/archive/resolve-deprecation-warnings-in-tests.md).
- Stabilized search ranking determinism with quantized tie-breaking,
  documented the fallback keys, and converted the ranking property test into
  deterministic fixtures that now pass without an XFAIL marker.

## [0.1.0a1] - Unreleased
- Local-first orchestrator coordinating multiple agents for research
  workflows.
- CLI, HTTP API, and Streamlit interfaces for executing queries.
- Hybrid DuckDB and RDF knowledge graph with plugin-based search backends.
- Prometheus metrics, interactive mode, and graph visualization utilities.
- Release remains pending while tests, coverage, and documentation builds are
  stabilized (see the issues referenced above and in [STATUS.md](STATUS.md)).
- Staged the packaging dry run with Python 3.12.10 and `uv 0.7.22`; archived the
  build log (`baseline/logs/build-20250924T033349Z.log`), the TestPyPI dry run
  log (`baseline/logs/publish-dev-20250924T033415Z.log`), and the recorded
  wheel and sdist checksums in [docs/release_plan.md](docs/release_plan.md).

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


