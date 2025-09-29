# Changelog

All notable changes to this project will be documented in this file.

Reference issues by slugged filename (for example,
`issues/archive/example-issue.md`) and avoid numeric prefixes.

## [Unreleased]
- Documented the Deep Research Enhancement Initiative phases in the roadmap and
  created `docs/deep_research_upgrade_plan.md` to coordinate adaptive gating,
  per-claim audits, GraphRAG, evaluation harnesses, and cost-aware routing
  ahead of implementation.
- Expanded the system specification and pseudocode to cover the adaptive gate,
  evidence pipeline 2.0, planner coordination, session GraphRAG, evaluation
  harness, and layered UX outputs.
- Opened coordination and execution tickets for the deep research upgrades to
  stage Phase 1 through Phase 5 deliverables before the alpha release.
- Refreshed release readiness documentation: `scripts/setup.sh` now appends the
  Task PATH helper automatically, `docs/releasing.md` explains the behaviour,
  and `docs/release_plan.md` now documents the successful
  `task release:alpha` sweep alongside the new verify, coverage, and build logs
  so auditors can trace the alpha sign-off.
  【F:scripts/setup.sh†L9-L93】【F:docs/releasing.md†L11-L15】
  【F:docs/release_plan.md†L18-L48】【F:baseline/logs/task-verify-20250930T174512Z.log†L1-L23】
  【F:baseline/logs/task-coverage-20250930T181947Z.log†L1-L21】【F:baseline/logs/python-build-20250929T030953Z.log†L1-L13】
- Logged the deep research phase tickets directly in the release narrative so
  their closure stays visible alongside the alpha acceptance criteria:
  [adaptive-gate-and-claim-audit-rollout](issues/archive/adaptive-gate-and-claim-audit-rollout.md),
  [planner-coordinator-react-upgrade](issues/planner-coordinator-react-upgrade.md),
  [session-graph-rag-integration](issues/session-graph-rag-integration.md),
  [evaluation-and-layered-ux-expansion](issues/evaluation-and-layered-ux-expansion.md),
  and [cost-aware-model-routing](issues/cost-aware-model-routing.md) align with
  [prepare-first-alpha-release](issues/prepare-first-alpha-release.md).
  【F:docs/release_plan.md†L18-L44】【F:issues/archive/adaptive-gate-and-claim-audit-rollout.md†L1-L42】
  【F:issues/planner-coordinator-react-upgrade.md†L1-L44】【F:issues/session-graph-rag-integration.md†L1-L44】
  【F:issues/evaluation-and-layered-ux-expansion.md†L1-L44】【F:issues/cost-aware-model-routing.md†L1-L44】
  【F:issues/prepare-first-alpha-release.md†L13-L34】

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
- Captured the September 30, 2025 `task release:alpha` sweep with clean verify,
  coverage, and packaging stages. The new logs show the scout gate telemetry,
  VSS loader, CLI path helper, and wheel build succeeding end-to-end, clearing
  the final blockers for alpha tagging.
  【F:baseline/logs/task-verify-20250930T174512Z.log†L1-L23】【F:baseline/logs/task-coverage-20250930T181947Z.log†L1-L21】
  【F:baseline/logs/python-build-20250929T030953Z.log†L1-L13】【F:issues/prepare-first-alpha-release.md†L1-L34】
- Logged consecutive `uv run task release:alpha` sweeps halting at
  `tests/unit/test_core_modules_additional.py::test_search_stub_backend` until
  the stub fixture accepts the optional `return_handles` argument, keeping the
  release gate open while the follow-up lands.【F:baseline/logs/release-alpha-20250924T183041Z.log†L20-L40】【F:baseline/logs/release-alpha-20250924T184646Z.summary.md†L1-L5】【F:baseline/logs/release-alpha-20250924T184646Z.log†L448-L485】
- Staged the packaging dry run with Python 3.12.10 and `uv 0.7.22`; archived the
  refreshed build log (`baseline/logs/build-20250924T033349Z.log`), the
  TestPyPI dry run log (`baseline/logs/publish-dev-20250924T033415Z.log`), and
  the wheel and sdist checksums in
  [docs/release_plan.md](docs/release_plan.md), closing
  [stage-0-1-0a1-release-artifacts](issues/archive/stage-0-1-0a1-release-artifacts.md).【F:baseline/logs/build-20250924T033349Z.log†L1-L13】【F:baseline/logs/publish-dev-20250924T033415Z.log†L1-L13】【F:STATUS.md†L33-L38】【F:issues/archive/stage-0-1-0a1-release-artifacts.md†L1-L40】

### Verification Evidence
- `uv run task verify` completed on 2025-09-25 at 02:27:17 Z after
  normalizing BM25 scoring, remapping the parallel execution payload maps, and
  making the numpy stub deterministic. The log documents the LRU eviction
  sequence and distributed executor remote case passing with VSS-enabled search
  instrumentation.
  【F:baseline/logs/task-verify-20250925T022717Z.log†L332-L360】
  【F:baseline/logs/task-verify-20250925T022717Z.log†L400-L420】
  【F:src/autoresearch/search/core.py†L705-L760】
  【F:src/autoresearch/orchestration/parallel.py†L145-L182】
  【F:tests/stubs/numpy.py†L12-L81】
- A targeted coverage rerun at 23:30:24 Z replayed the distributed executor and
  storage suites with those fixes; the focused log records the formerly blocking
  parametrisations passing while we schedule a full extras sweep on refreshed
  runners.
  【F:baseline/logs/task-coverage-20250925T233024Z-targeted.log†L1-L14】
  【F:src/autoresearch/search/core.py†L705-L760】
  【F:src/autoresearch/orchestration/parallel.py†L145-L182】
  【F:tests/stubs/numpy.py†L12-L81】

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


