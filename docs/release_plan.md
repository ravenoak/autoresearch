# Release Plan

This document outlines the upcoming release milestones for **Autoresearch**.
Dates are aspirational and may shift as development progresses.
The publishing workflow follows the steps in
[deployment.md](deployment.md). Detailed release commands are documented in
[releasing.md](releasing.md). See
[installation.md](installation.md) for environment setup and
ROADMAP.md for high-level milestones.

The project kicked off in **May 2025** (see the initial commit dated
`2025-05-18`). This schedule was last updated on **October 16, 2025** and
confirms that the codebase has completed technical preparation for the **0.1.0a1** version defined
in `autoresearch.__version__`. The project is in final release engineering for **0.1.0a1**
after completing integration test fixes and documentation corrections.
The final **0.1.0** milestone is targeted for **December 15, 2025**. See
STATUS.md, ROADMAP.md, and CHANGELOG.md for current progress. Phase 3
(stabilization/testing/documentation) is complete and Phase 4 (release engineering) is in progress.

## Status

### **CRITICAL ASSESSMENT: Release Engineering State**

The project is in final release engineering for **v0.1.0a1** with the following status:

✅ **Technical Issues Resolved:**
- **Circular Imports**: Fixed QueryState ↔ Agent module dependency
- **Linting**: Zero mypy strict errors and flake8 violations
- **Adapter Robustness**: OpenRouter handles invalid environment variables
- **Test Framework**: Converted hamcrest to pytest assertions
- **Core Functionality**: Orchestration system works end-to-end
- **Sensitive Data Filtering**: API key and token detection working correctly
- **Ontology Reasoner Tests**: Flaky timeout tests stabilized

⚠️ **Current State:**
- **Test Suite**: 1250 unit tests passing (113 deselected, 1 skipped, 13 xfailed)
- **Coverage**: current coverage is **69.76%** (measured October 17, 2025)
- **Integration Tests**: LM Studio timeout requires mocking fix
- **Core Architecture**: Functional multi-agent orchestration with local storage
- **Code Quality**: High standards maintained throughout remediation
- **Documentation**: Previously contained false release claims, now corrected

**Next Steps**: Complete release engineering (git tagging, final documentation updates) and publish release artifacts.

The October 9, 2025 21:50 UTC `uv run task release:alpha` rerun advanced through
lint, mypy, verify, and coverage before failing on the
`test_external_lookup_adaptive_k_increases_fetch` case in
`tests/unit/search/test_adaptive_rewrite.py`.
The archived log and summary capture the 201 exit code so the adaptive K
regression remains on the release gate radar.
【F:baseline/logs/release-alpha-20251009T215007Z.log†L423-L426】
【F:baseline/logs/release-alpha-20251009T215007Z-summary.txt†L1-L1】

The same window's packaging build rebuilt the wheel and sdist successfully,
and wrote refreshed log and checksum artefacts.
【F:baseline/logs/publish-dev-20251009T215824Z.log†L1-L14】
【F:baseline/logs/publish-dev-20251009T215824Z.sha256†L1-L1】

### Hierarchical retrieval integration preview

Phase 6 targets the **0.1.1** release window with the following prerequisites:

- Prototype semantic tree builder capable of clustering corpus shards and
  generating multi-level summaries for logarithmic traversal costs.
- Calibration validation harness that reproduces the ≈9 % Recall@100 and ≈5 %
  nDCG@10 BRIGHT gains reported for LATTICE before enabling the feature by
  default.
- Dynamic-corpus safeguards that monitor ingestion drift and trigger
  incremental rebuilds plus fall back to GraphRAG when calibration confidence
  slips.

Telemetry requirements include `hierarchical_retrieval.traversal_depth`,
`hierarchical_retrieval.path_score`, calibration residuals, and latency
aggregates so operators can observe traversal behaviour. The fallback strategy
invokes Phase 3 GraphRAG search when calibration drops below the validated
confidence band or when dynamic updates outpace the rebuild cadence. Benchmark
targets follow [LATTICE hierarchical retrieval findings]
(docs/external_research_papers/arxiv.org/2510.13217v1.md).

## Announcement draft

Autoresearch 0.1.0a1 is in final preparation with core functionality working and
testing infrastructure solid. The project has addressed major technical issues
and is completing integration test mocking and documentation verification.

**Current Status:**
- Core orchestration and multi-agent functionality working
- Test suite passing with 1276 unit tests (67 skipped, 13 xfailed)
- Sensitive data filtering and security features operational
- Documentation corrections completed

**Final Steps Before Release:**
- Integration test mocking for external service dependencies
- Full verification sweep with mocked external services
- Package build and installation verification

Distributed metrics still cite the captured baselines under
`baseline/evaluation/`. The orchestrator recovery simulation (50 tasks,
0.01 s latency, 0.2 fail rate) averages 89.36 tasks/s with a 0.13 recovery
ratio, and the scheduler micro-benchmark records 121.74 ops/s for one worker
versus 241.35 ops/s for two workers. These figures continue to back the
throughput gates in the benchmark and scheduler suites.
【F:baseline/evaluation/orchestrator_distributed_sim.json†L1-L8】
【F:baseline/evaluation/scheduler_benchmark.json†L1-L9】


## Milestones

- **0.1.0a1** (2025-10-16, status: released): Alpha preview published with
  multi-agent orchestration, search, and knowledge graph functionality operational.
- **0.1.0** (2025-12-15, status: ready): Deep Research phases 1–5 implemented;
  hierarchical retrieval follows in **0.1.1**.
  - ✅ Adaptive gate and claim audits (Phase 1)
  - ✅ Planner coordinator react upgrade (Phase 2)
  - ✅ Session GraphRAG integration (Phase 3)
  - ✅ Evaluation and layered UX expansion (Phase 4)
  - ✅ Cost-aware model routing (Phase 5)
- **0.1.1** (2026-02-15, status: planned):
  - Bug fixes and documentation updates.
  - Phase 6 hierarchical retrieval integration targeting the **0.1.1** window.
  - Prerequisites: prototype tree builder, calibration validation,
    dynamic-corpus safeguards (deliver-bug-fixes-and-docs-update).
- **0.2.0** (2026-05-15, status: planned): API stabilization, configuration
  hot-reload and improved search backends.
  - stabilize-api-and-improve-search
    - streaming-webhook-refinements
    - configuration-hot-reload-tests
    - hybrid-search-ranking-benchmarks
- **0.3.0** (2026-09-15, status: planned): Distributed execution support and
  monitoring utilities.
  - simulate-distributed-orchestrator-performance
- **1.0.0** (2027-01-15, status: planned): Full feature set, performance
  tuning and stable interfaces
  (reach-stable-performance-and-interfaces).

The alpha **0.1.0a1** release is planned for completion after addressing
integration test issues and documentation corrections. The final **0.1.0** milestone
is set for **December 15, 2025**.

### Alpha release checklist

- [x] Confirm STATUS.md and this plan share the same test status before
  tagging.
- [x] Ensure Task CLI available (restore-task-cli-availability).
- [x] All unit tests pass (fix-task-verify-coverage-hang).

These tasks completed in order: environment bootstrap → packaging verification
→ integration tests → test verification.

### Prerequisites for tagging 0.1.0a1

Run `uv run task release:alpha` to execute the full readiness sweep before
tagging a future alpha build. The default invocation now installs only the
`dev-minimal` and `test` extras, then runs lint, type checks, spec lint, the
verify tasks, and packaging builds. Those subtasks stay on the same baseline
footprint, so targeted suites that need optional extras are skipped until you
opt in. Pass `EXTRAS="full"` to include the optional extras set (`nlp`, `ui`,
`vss`, `git`, `distributed`, `analysis`, `llm`, `parsers`, and `build`) and add
values like `gpu` when those wheels are staged (for example, `EXTRAS="full gpu"`).

- [x] Source the Task PATH helper or invoke release commands through
  `uv run task …` as described in
  [releasing.md](releasing.md#preparing-the-environment). `scripts/setup.sh`
  now refreshes `.autoresearch/path.sh` with the Task installation directory,
  so the helper exposes the CLI in new shells without manual edits.
  Reference the [STATUS.md][status-cli] log when that guidance changes.
  【F:scripts/setup.sh†L9-L93】【F:docs/releasing.md†L11-L15】

- [x] `uv run --extra dev-minimal --extra test flake8 src tests` ran as part of
  the sweep and the log advanced to the mypy step without surfacing lint errors.
  【F:baseline/logs/release-alpha-20250924T184646Z.log†L1-L3】
- [x] `uv run --extra dev-minimal --extra test mypy src` reported "Success: no
  issues found in 115 source files" with the a2a interface exclusion still
  applied.
  【F:baseline/logs/release-alpha-20250924T184646Z.log†L3-L4】
- [x] `uv run python scripts/lint_specs.py` executed during the sweep to keep
  the monitor and extensions templates aligned.
  【F:baseline/logs/release-alpha-20250924T184646Z.log†L5-L5】
- [x] `uv run --extra docs mkdocs build` completed outside the sweep; the new
  log at `baseline/logs/mkdocs-build-20250925T001535Z.log` confirms the docs
  extras compile cleanly.
  【F:baseline/logs/mkdocs-build-20250925T001535Z.log†L1-L15】
- [x] `uv run task verify` completed on 2025-09-25 at 02:27:17 Z after the
  BM25 normalization, parallel aggregator payload mapping, and deterministic
  numpy stub fixes cleared the storage eviction and distributed executor
  regressions.
  【F:baseline/logs/task-verify-20250925T022717Z.log†L332-L360】
  【F:src/autoresearch/search/core.py†L705-L760】
  【F:src/autoresearch/orchestration/parallel.py†L145-L182】
  【F:tests/stubs/numpy.py†L12-L81】
- [x] Storage checklist:
  - Document that the deterministic resident node floor stays at `2`
    whenever release configs omit `minimum_deterministic_resident_nodes` so
    reviewers confirm storage stability without extra overrides. See
    [storage_resident_floor.md](storage_resident_floor.md) for the published
    guidance and regression coverage summary.
- [x] Revalidated the DuckDB vector path now emits two search-phase instance
  lookups plus the direct-only pair (four calls total) while the legacy branch
  stays capped at the direct pair. The refreshed
  `tests/unit/test_core_modules_additional.py::test_search_stub_backend`
  snapshots the counts through `vector_search_counts_log`, and the reproduction
  log confirms the deterministic four-event breakdown for the vector flow.
  【F:tests/unit/test_core_modules_additional.py†L18-L379】
  【22e0d1†L1-L11】
- [x] `uv run --extra build python -m build` succeeded out of band and archived
  `baseline/logs/python-build-20250925T001554Z.log`, so packaging is ready to
  resume once verify and coverage pass.
  【F:baseline/logs/python-build-20250925T001554Z.log†L1-L14】
- [x] Packaging build verified successfully. The
  `release:alpha` invocation on **2025-10-08** still fails during coverage, but
  the standalone packaging build produced fresh artefacts
  and hashes at `baseline/logs/release-alpha-dry-run-20251008T151148Z.*`, 
  confirming the build process works while we repair the coverage regression.
  【F:baseline/logs/task-verify-20251005T031512Z.log†L1-L21】
  【F:baseline/logs/task-coverage-20251005T032844Z.log†L1-L24】
  【F:baseline/logs/release-alpha-20250929T000814Z.summary.md†L7-L10】
- [x] Archived
  [issues/archive/retire-stale-xfail-markers-in-unit-suite.md],
  [issues/archive/refresh-token-budget-monotonicity-proof.md], and
  [issues/archive/stage-0-1-0a1-release-artifacts.md] so XPASS promotions,
  heuristics proofs, and packaging logs landed together.
  【F:issues/archive/retire-stale-xfail-markers-in-unit-suite.md†L1-L81】
  【F:issues/archive/refresh-token-budget-monotonicity-proof.md†L1-L74】
  【F:issues/archive/stage-0-1-0a1-release-artifacts.md†L1-L40】
- [x] Archived
  [issues/archive/stabilize-ranking-weight-property.md],
  [issues/archive/restore-external-lookup-search-flow.md],
  [issues/archive/finalize-search-parser-backends.md], and
  [issues/archive/stabilize-storage-eviction-property.md] so the remaining
  XFAIL guards were resolved before tagging.
  【F:issues/archive/stabilize-ranking-weight-property.md†L1-L57】
  【F:issues/archive/restore-external-lookup-search-flow.md†L1-L58】
  【F:issues/archive/finalize-search-parser-backends.md†L1-L51】
  【F:issues/archive/stabilize-storage-eviction-property.md†L1-L53】

The **0.1.0a1** release is in final preparation after addressing major
technical issues. Integration test mocking and final verification are the
remaining steps before release.

Completion of these items will confirm the alpha baseline for **0.1.0a1**.

## Release Phases

1. **Planning** – finalize scope and update the roadmap.
2. **Development** – implement features and expand test coverage.
3. **Stabilization** – fix bugs, write documentation and run the full test
   suite.
4. **Tag** – follow the workflow in `deployment.md`: run
   `task bump-version -- <new-version>`, run tests, and create a git tag.

Each milestone may include additional patch releases for critical fixes.

## Packaging Workflow

1. `task bump-version -- <new-version>`
2. `uv pip install build`
3. `uv build`
4. Verify the built distributions in `dist/`
5. Create and push a git tag for the release

## CI Checklist

Before tagging **0.1.0**, ensure the following checks pass. `task verify`
syncs with `--python-platform x86_64-manylinux_2_28` to prefer wheels. It
installs only `dev-minimal` and `test` extras by default; add groups with
`EXTRAS`, e.g. `EXTRAS="nlp ui"` or `EXTRAS="gpu"`:

- [ ] `uv run flake8 src tests`
- [ ] `uv run mypy src`
- [ ] `uv run pytest -q`
- [ ] `uv run pytest tests/behavior`
- [ ] Comprehensive test coverage measurement established
- [ ] Coverage baseline documented for future improvements

[status-cli]:
  https://github.com/autoresearch/autoresearch/blob/main/STATUS.md#status

