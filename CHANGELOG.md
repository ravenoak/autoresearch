# Changelog

All notable changes to this project will be documented in this file.

Reference issues by slugged filename (for example,
`issues/archive/example-issue.md`) and avoid numeric prefixes.

## [Unreleased]
- No unreleased changes since the 0.1.0a1 staging summary.

## [0.1.0a1] - Unreleased
- Local-first orchestrator coordinating multiple agents for research
  workflows.
- CLI, HTTP API, and Streamlit interfaces for executing queries.
- Hybrid DuckDB and RDF knowledge graph with plugin-based search backends.
- Prometheus metrics, interactive mode, and graph visualization utilities.
- The 0.1.0a1 tag is staged pending final release sign-off after verifying the
  gating work recorded below and in [STATUS.md](STATUS.md).

### Blocker Resolutions
- Bucketed relevance scores at a :math:`10^{-6}` resolution to preserve
  deterministic tie-breaking, exposed the bucket metadata for property and
  idempotence regressions, refreshed the relevance ranking algorithm note, and
  recorded the guarantee in the spec coverage ledger, addressing
  [stabilize-ranking-weight-property](issues/archive/stabilize-ranking-weight-property.md).【F:src/autoresearch/search/core.py†L199-L203】【F:src/autoresearch/search/core.py†L803-L880】【F:tests/unit/test_property_search_ranking.py†L12-L235】【F:tests/unit/test_ranking_idempotence.py†L1-L53】【F:tests/unit/test_relevance_ranking.py†L372-L414】【F:docs/algorithms/relevance_ranking.md†L40-L49】【F:SPEC_COVERAGE.md†L64-L64】【F:SPEC_COVERAGE.md†L263-L263】
- Retired the remaining search, distributed, and budgeting XFAIL markers,
  refreshing the corresponding docs/algorithms entries, SPEC_COVERAGE.md, and
  changelog coverage to lock in the XPASS promotions, closing
  [retire-stale-xfail-markers-in-unit-suite](issues/archive/retire-stale-xfail-markers-in-unit-suite.md).【F:docs/algorithms/distributed.md†L19-L30】【F:docs/algorithms/relevance_ranking.md†L75-L83】【F:docs/algorithms/semantic_similarity.md†L24-L34】【F:docs/algorithms/cache.md†L24-L37】【F:docs/algorithms/token_budgeting.md†L159-L169】【F:SPEC_COVERAGE.md†L23-L64】
- Finalized PDF and DOCX ingestion for 0.1.0a1 by expanding regression
  coverage across dependency failures and text normalization, updating the
  spec ledger, and aligning README plus installation guidance with the optional
  parsers extra, addressing
  [finalize-search-parser-backends](issues/archive/finalize-search-parser-backends.md).【F:tests/unit/test_search_parsers.py†L55-L172】【F:README.md†L214-L245】【F:docs/installation.md†L105-L170】【F:SPEC_COVERAGE.md†L65-L65】【F:SPEC_COVERAGE.md†L250-L268】
- Restored the storage-backed hybrid lookup flow by exposing
  `StorageManager` and `get_cache` through `autoresearch.search`, adding the
  `ExternalLookupResult` bundle for `return_handles=True`, rehydrating vector,
  BM25, and ontology signals during `Search.external_lookup`, and promoting the
  vector and hybrid query regressions with documentation and spec updates,
  closing
  [restore-external-lookup-search-flow](issues/archive/restore-external-lookup-search-flow.md).【F:src/autoresearch/search/__init__.py†L1-L38】【F:src/autoresearch/search/core.py†L70-L112】【F:src/autoresearch/search/core.py†L1326-L1496】【F:docs/algorithms/search.md†L49-L70】【F:docs/algorithms/cache.md†L27-L41】【F:docs/specs/search.md†L23-L44】【F:tests/unit/test_search.py†L296-L340】【F:SPEC_COVERAGE.md†L64-L64】
- Stabilized storage eviction by documenting the stale-LRU counterexample,
  adding a fallback when caches are empty, extending the property-based
  regression, and introducing a `stale_lru` simulation scenario, closing
  [stabilize-storage-eviction-property](issues/archive/stabilize-storage-eviction-property.md).【F:src/autoresearch/storage.py†L803-L836】【F:tests/unit/test_storage_eviction.py†L63-L195】【F:tests/unit/test_storage_eviction_sim.py†L1-L76】【F:scripts/storage_eviction_sim.py†L1-L246】【F:docs/algorithms/storage_eviction.md†L31-L96】【F:docs/specs/storage.md†L32-L65】【F:SPEC_COVERAGE.md†L67-L67】
- Captured the Hypothesis metrics-dropout regression for `_enforce_ram_budget`,
  ensured deterministic caps continue when RAM metrics vanish mid-run, seeded
  the property and simulation with the regression seed, refreshed the storage
  docs, and updated spec coverage to remove the guard.【F:src/autoresearch/storage.py†L596-L606】【F:tests/unit/test_storage_eviction.py†L63-L195】【F:tests/unit/test_storage_eviction_sim.py†L1-L76】【F:scripts/storage_eviction_sim.py†L1-L246】【F:docs/algorithms/storage_eviction.md†L31-L96】【F:docs/specs/storage.md†L32-L65】【F:SPEC_COVERAGE.md†L67-L67】
- Documented the token budget dialectic by recording the zero-history
  counterexample, codifying the piecewise specification, refreshing the
  metrics review, adding deterministic regressions, updating spec coverage, and
  lifting the former `xfail` guard for
  [refresh-token-budget-monotonicity-proof](issues/archive/refresh-token-budget-monotonicity-proof.md).【F:docs/algorithms/token_budgeting.md†L93-L142】【F:docs/specs/token-budget.md†L20-L59】【F:docs/specs/metrics.md†L44-L67】【F:tests/unit/test_heuristic_properties.py†L25-L59】【F:SPEC_COVERAGE.md†L59-L59】
- Archived [resolve-deprecation-warnings-in-tests](issues/archive/resolve-deprecation-warnings-in-tests.md) after removing the
  repository-wide `pkg_resources` suppression from `sitecustomize.py` and
  capturing a clean `task verify:warnings:log` run at
  `baseline/logs/verify-warnings-20250923T224648Z.log`.【F:sitecustomize.py†L1-L37】【F:baseline/logs/verify-warnings-20250923T224648Z.log†L1047-L1047】【F:baseline/logs/verify-warnings-20250923T224648Z.log†L1442-L1442】【F:baseline/logs/verify-warnings-20250923T224648Z.log†L1749-L1749】
- Documented deterministic eviction fallback when OS metrics are unavailable
  and enforced ranking weight sums before normalization across the storage and
  search modules.【F:src/autoresearch/storage.py†L596-L606】【F:src/autoresearch/search/core.py†L803-L880】
- Migrated integration tests to use `content=` with `httpx`, pinned the
  dependency to the 0.28.x series, and recorded the `content` deprecation
  warning in
  [resolve-deprecation-warnings-in-tests](issues/archive/resolve-deprecation-warnings-in-tests.md).【F:tests/integration/test_api_auth_middleware.py†L6-L29】【F:issues/archive/resolve-deprecation-warnings-in-tests.md†L1-L103】
- Prevented overweight search ranking vectors from being silently normalised by
  raising a `ConfigError` and documenting the behaviour in
  [docs/specs/config.md](docs/specs/config.md).【F:src/autoresearch/search/core.py†L803-L880】【F:docs/specs/config.md†L1-L57】
- Logged the config weight validation regression in
  [fix-config-weight-sum-validation](issues/archive/fix-config-weight-sum-validation.md).【F:issues/archive/fix-config-weight-sum-validation.md†L1-L39】
- Captured offline DuckDB extension fallback failures in
  [fix-duckdb-extension-offline-fallback](issues/archive/fix-duckdb-extension-offline-fallback.md).【F:issues/archive/fix-duckdb-extension-offline-fallback.md†L1-L32】
- Narrowed the search regression scope in
  [fix-search-ranking-and-extension-tests](issues/archive/fix-search-ranking-and-extension-tests.md), which now focuses on
  aligning the overweight ranking unit test with the validator while extension
  loader suites pass.【F:issues/archive/fix-search-ranking-and-extension-tests.md†L1-L39】
- Continued to track documentation build warnings in
  [fix-mkdocs-griffe-warnings](issues/archive/fix-mkdocs-griffe-warnings.md).【F:issues/archive/fix-mkdocs-griffe-warnings.md†L1-L37】
- Replaced deprecated `fastembed.TextEmbedding` imports with the new
  `OnnxTextEmbedding` entry point, updated stubs and tests to mirror the public
  API, and noted the migration in
  [resolve-deprecation-warnings-in-tests](issues/archive/resolve-deprecation-warnings-in-tests.md).【F:src/autoresearch/search/parsers.py†L1-L200】【F:tests/unit/test_search_parsers.py†L55-L172】【F:issues/archive/resolve-deprecation-warnings-in-tests.md†L1-L103】
- Stabilized search ranking determinism with quantized tie-breaking,
  documented the fallback keys, and converted the ranking property test into
  deterministic fixtures that now pass without an XFAIL marker.【F:src/autoresearch/search/core.py†L199-L203】【F:src/autoresearch/search/core.py†L803-L880】【F:tests/unit/test_property_search_ranking.py†L12-L235】【F:tests/unit/test_ranking_idempotence.py†L1-L53】

### Packaging Staging
- Staged the packaging dry run with Python 3.12.10 and `uv 0.7.22`; archived the
  build log (`baseline/logs/build-20250924T172531Z.log`), the TestPyPI dry run
  log (`baseline/logs/publish-dev-20250924T172554Z.log`), and the refreshed
  wheel and sdist checksums in [docs/release_plan.md](docs/release_plan.md),
  closing
  [stage-0-1-0a1-release-artifacts](issues/archive/stage-0-1-0a1-release-artifacts.md).【F:baseline/logs/build-20250924T172531Z.log†L1-L13】【F:baseline/logs/publish-dev-20250924T172554Z.log†L1-L14】【F:docs/release_plan.md†L92-L129】【F:issues/archive/stage-0-1-0a1-release-artifacts.md†L1-L40】

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


