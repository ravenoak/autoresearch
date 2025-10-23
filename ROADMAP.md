# Autoresearch Roadmap

This roadmap summarizes planned features for upcoming releases.
Dates and milestones align with the [release plan](docs/release_plan.md).
See [STATUS.md](STATUS.md) and [CHANGELOG.md](CHANGELOG.md) for current results
and recent changes. Installation and environment details are covered in the
[README](README.md). Last updated **October 23, 2025** after harmonising
coverage, test-count, and release-status reporting across the documentation
set.


As of **October 23, 2025 05:41 UTC**, the latest coverage export reports
**71.94 %** line coverage (15,786 of 21,943 lines) from the October 17, 2025
17:14 UTC `coverage.xml` run, and the October 22, 2025 19:13 UTC pytest
collection baseline enumerates **1,907 tests** with **167 deselected** during
collection. Release engineering for **v0.1.0a1** remains paused until the suite
is green.

## Deep Research enhancement program

The September 26 dialectical review produced a five-phase execution plan to
raise factuality while containing cost and latency. Each phase is tracked by a
dedicated in-repo ticket so progress can be audited without leaving the
repository:

1. [adaptive-gate-and-claim-audit-rollout](issues/archive/adaptive-gate-and-claim-audit-rollout.md)
   – implements the scout pass, gate policy signals, and per-claim audit
   tables. **✅ COMPLETE - Released in v0.1.0a1**
2. [planner-coordinator-react-upgrade](issues/planner-coordinator-react-upgrade.md)
   – elevates decomposition into a schedulable task graph with ReAct telemetry.
   **✅ COMPLETE - Task graphs, coordinator, ReAct traces implemented**
3. [session-graph-rag-integration](issues/session-graph-rag-integration.md)
   – constructs session graphs, contradiction checks, and exportable artifacts.
   **✅ COMPLETE - Graph exports, visualization, contradiction signals implemented**
4. [evaluation-and-layered-ux-expansion](issues/evaluation-and-layered-ux-expansion.md)
   – widens the benchmark harness, layered output options, and Socratic
   controls. **✅ COMPLETE - TruthfulQA/FEVER/HotpotQA harness, layered output controls implemented**
5. [cost-aware-model-routing](issues/cost-aware-model-routing.md) – introduces
   role-aware model selection, budgets, and telemetry to demonstrate savings.
   **✅ COMPLETE - Budget-aware routing, latency SLOs implemented**
6. [hierarchical-retrieval-lattice-integration](issues/hierarchical-retrieval-lattice-integration.md)
   – integrates a prototype LATTICE-style semantic tree and calibration harness.
   – Prerequisites: prototype tree builder, calibration validation, dynamic-
     corpus safeguards.
   – Default experiment settings: Gemini 2.5-flash, beam width `B=2`,
     `N=20` leaf expansions, depth limit `ℓ=10`, branching factor 10–20,
     approximating 250 explored nodes per query.
   – Risk note: dynamic, query-dependent corpora demand rapid summary refreshes
     or GraphRAG fallback, as highlighted by the BRIGHT coding subsets
     regression outcome.
   – Targets the **0.1.1** release window with telemetry and fallback guardrails.
   – Milestone acceptance requires reproducing ≥9 % Recall@100 and ≥5 %
     nDCG@10 uplift, with telemetry capturing cross-branch calibration
     residuals.
   – **🚧 IN PROGRESS - Pending prototype tree builder, calibration validation, and
     dynamic-corpus safeguards**

**Phases 1–5 are complete for v0.1.0; Phase 6 extends the roadmap toward v0.1.1.**

These tickets align with [docs/deep_research_upgrade_plan.md](docs/deep_research_upgrade_plan.md)
and the updated specification so release milestones can absorb the upgrades in
measured increments. Phases 1–5 embed verification loops, retrieval exports,
task graphs, GraphRAG, evaluation harnesses, and cost-aware routing, while
Phase 6 layers hierarchical retrieval evaluation, telemetry, and fallbacks onto
that foundation.
【F:src/autoresearch/orchestration/reverify.py†L73-L197】
【F:tests/unit/orchestration/test_reverify.py†L1-L80】
【F:tests/behavior/features/reasoning_modes.feature†L8-L22】
【F:src/autoresearch/knowledge/graph.py†L113-L204】
【F:src/autoresearch/search/context.py†L618-L666】
【F:src/autoresearch/orchestration/state.py†L1120-L1135】
【F:tests/unit/storage/test_knowledge_graph.py†L1-L63】
【F:src/autoresearch/cli_evaluation.py†L1-L121】
【F:src/autoresearch/orchestration/task_graph.py†L1-L315】
【F:src/autoresearch/orchestration/model_routing.py†L1-190】

Phases 1–5 provide the foundation for the **v0.1.0** release. Phase 6
hierarchical retrieval is staged for **0.1.1** once the prototype tree builder,
calibration validation, and dynamic-corpus safeguards finish implementation and
the telemetry plus GraphRAG fallback strategy prove stable against the
LATTICE-derived targets.
Technical work for 0.1.0 is still being stabilised; verify and coverage runs
remain red, so release artifacts have not been validated and git tagging is on
hold.

## Research federation enhancements

The staged federation roadmap follows
[docs/specs/research_federation_enhancements.md](docs/specs/research_federation_enhancements.md)
and maps to requirements F-28 through F-31. Delivery spans three incremental
drops so workspace-aware tooling can reach production while retaining fallbacks
for earlier flows:

1. **Phase RF-1 — Manifest persistence (Complete)**
   - Introduces versioned workspace manifests in DuckDB and persistence hooks in
     `StorageManager.save_workspace_manifest`.
   - Covers requirement **F-28** with unit coverage in
     `tests/unit/storage/test_workspace_manifest.py`.
   - Lands in **0.1.1** to unblock downstream orchestration work.
2. **Phase RF-2 — Workspace orchestration (In progress)**
   - Wraps the orchestrator with manifest injection and coverage enforcement,
     ensuring contrarian and fact-checker roles cite required resources.
   - Satisfies **F-29** with `WorkspaceOrchestrator` unit tests and behavior
     scenarios in `tests/behavior/features/research_federation.feature`.
   - Ships `autoresearch search manifest` subcommands so analysts can curate
     multi-repository manifests without editing configuration files manually.
   - Targets **0.1.1** with a beta tag after coverage telemetry stabilises.
3. **Phase RF-3 — Federated UX and scholarly cache (Planned)**
   - Expands the CLI surface with `autoresearch workspace` flows, extends the
     desktop workspace panel, and layers in scholarly connector caching for
     offline replay.
   - Maps to **F-30** and **F-31**, validated through desktop integration tests
     and the research federation behavior suite.
   - Ships in **0.1.2** once the scholarly connector cache is populated and UX
     fallbacks are verified.

Each phase keeps pre-existing CLI and desktop behavior as a fallback when the
workspace-aware orchestrator is disabled. The milestones align with
`STATUS.md` tracking so that telemetry, cache management, and manifest versioning
graduate together without blocking release operations.

## Status

See [STATUS.md](STATUS.md) for detailed logs and
[CHANGELOG.md](CHANGELOG.md) for recent updates. As of **October 23, 2025
05:41 UTC**, the v0.1.0a1 rehearsal remains paused: the latest coverage export
reports 71.94 % (15,786 of 21,943 lines) from the October 17, 2025 17:14 UTC
`coverage.xml`, and the October 22, 2025 19:13 UTC pytest collection baseline
enumerates 1,907 tests with 167 deselected. Verify and coverage are still red,
no `v0.1.0a1` tag exists, and the alpha ticket tracks the open checklist.
coverage sweep are the next gates. The updated
[preflight readiness plan](docs/v0.1.0a1_preflight_plan.md) marks PR-S1,
PR-S2, and PR-R0 complete while prioritising lint cleanup and coverage reruns;
the alpha ticket mirrors the same checklist.
【F:docs/v0.1.0a1_preflight_plan.md†L1-L210】【F:issues/prepare-first-alpha-release.md†L1-L64】

The deterministic storage resident-floor documentation remains published and
linked from the release plan while coverage and verification sweeps are refreshed.
【F:docs/storage_resident_floor.md†L1-L23】【F:docs/release_plan.md†L324-L356】

Phase 1 of the deep research initiative is still complete. Upcoming work
focuses on the PR slices described in the preflight plan so AUTO telemetry,
planner prompts, and retrieval upgrades land once the test suite is green.
【F:docs/v0.1.0a1_preflight_plan.md†L115-L173】

## Milestones

- 0.1.0a1 (target 2025-10-16, status: blocked on verify/coverage): Alpha
  preview awaiting a green suite and packaging artefact capture.
- 0.1.0 (2025-12-15, status: planned): Finalised packaging, docs, and CI
  checks once alpha tagging evidence is complete.
- 0.1.1 (2026-02-15, status: planned): Bug fixes and documentation updates.
- 0.2.0 (2026-05-15, status: planned): API stabilization, configuration
  hot-reload and improved search backends.
- 0.3.0 (2026-09-15, status: planned): Distributed execution support and
  monitoring utilities.
  - 1.0.0 (2027-01-15, status: planned): Full feature set, performance tuning
    and stable interfaces.
  - Stability goals monitor the alpha coordination and archived verification
    work:
    - [prepare-first-alpha-release]
    - [resolve-resource-tracker-errors-in-verify (archived)][resolve-resource-archived]
    - [resolve-deprecation-warnings-in-tests (archived)][resolve-deprecation-archived]
    - [rerun-task-coverage-after-storage-fix (archived)][rerun-coverage-archived]
  - The spec template lint cleanup is archived as
    [spec lint template ticket (archived)][restore-spec-lint-template-compliance-archived],
    so the coverage rerun ticket inherits the remaining release check.

See [docs/release_plan.md](docs/release_plan.md#alpha-release-checklist)
for the alpha release checklist.

[prepare-first-alpha-release]: issues/prepare-first-alpha-release.md
[clean-up-flake8]: issues/archive/clean-up-flake8-regressions-in-routing-and-search-storage.md
[resolve-resource-archived]: issues/archive/resolve-resource-tracker-errors-in-verify.md
[resolve-deprecation-archived]: issues/archive/resolve-deprecation-warnings-in-tests.md
[rerun-coverage-archived]: issues/archive/rerun-task-coverage-after-storage-fix.md
[address-storage-archived]: issues/archive/address-storage-setup-concurrency-crash.md
[restore-dist-archived]: issues/archive/restore-distributed-coordination-simulation-exports.md
[restore-spec-lint-template-compliance-archived]:
  issues/archive/restore-spec-lint-template-compliance.md

## 0.1.0a1 – Alpha preview

This alpha release remains in preparation while the verification and coverage
gates are red. Related issue
([prepare-first-alpha-release](issues/prepare-first-alpha-release.md)) tracks
the work. Tagging **0.1.0a1** requires finishing verify, coverage, packaging,
and documentation updates; no release artifacts or git tags have been published
yet.
Key activities include:

- [x] Environment bootstrap documented and installation instructions
  consolidated.
- [x] Task CLI availability restored.
- [x] Packaging verification with DuckDB fallback.
- [x] DuckDB extension fallback hardened for offline setups.
- [x] Distributed coordination helpers restored
  ([restore-distributed-coordination simulation exports (archived)][restore-dist-archived]).
- [ ] `task verify` runs cleanly without cache flake or adaptive rewrite
  regressions (current blockers tracked in
  [prepare-first-alpha-release]).
- [x] Deprecation warnings removed from test runs
  ([resolve-deprecation-warnings-in-tests (archived)][resolve-deprecation-archived]).
- [ ] Coverage and release packaging finalized for the alpha tag
  ([prepare-first-alpha-release]).
- [x] Storage setup concurrency crash resolved
  ([address-storage-setup-concurrency-crash (archived)][address-storage-archived]).
- [x] Algorithm validation for ranking and coordination.
- [x] Formal validation for the OxiGraph backend.

These steps proceed in sequence: environment bootstrap → packaging
verification → integration tests → coverage gates → algorithm validation.

## 0.1.0 – First public preview

The final 0.1.0 release focuses on making the project installable and
providing complete documentation once the open issues are resolved. Key
activities include:

- Running all unit, integration and behavior tests (see [STATUS.md](STATUS.md)).
- Finalizing API reference and user guides.
- Verifying packaging metadata.
- Document domain model for agents, queries, storage, and search.

Type checking and unit tests currently fail; see [STATUS.md](STATUS.md) for
details. The **0.1.0** milestone is targeted for **December 15, 2025** while
packaging tasks are resolved.

## 0.1.1 – Bug fixes and documentation updates

Before publishing 0.1.0 the release plan lists several checks:

- Verify all automated tests pass in CI.
- Review documentation for clarity using a Socratic approach.
- Conduct a dialectical evaluation of core workflows.
- Ensure packaging metadata and publish scripts work correctly.

Any remaining issues from these tasks will be addressed in 0.1.1.

- CLI backup commands and testing utilities remain pending, while specialized
  agents—Moderator, Specialist, and User—are already implemented
  (`src/autoresearch/agents/specialized/moderator.py`,
  `src/autoresearch/agents/specialized/domain_specialist.py`,
  `src/autoresearch/agents/specialized/user_agent.py`) and will receive
  comprehensive unit   tests once testing passes. The 0.1.1 release is planned for
  **February 15, 2026**.

## Deep Research Enhancement Initiative (2025-2026)

The September 26, 2025 dialectical review produced a five-phase plan to raise
truthfulness, verifiability, and research depth. See
[Deep Research Upgrade Plan](docs/deep_research_upgrade_plan.md) for complete
details. The phases integrate with existing milestones as follows:

1. **Phase 1 – Adaptive Gate and Claim Audits** (feeds alpha readiness)
   - Implement scout pass signals, gating policy, and per-claim audit exports.
   - Update response schemas and clients to display audit tables.
   - Extend behavior coverage with the AUTO planner → scout gate → verify loop
     so gate decisions and audit badges remain observable in CI, including the
     CLI entrypoint to validate telemetry for debate escalation and verification
     loops.
   - Track metrics for early-exit accuracy and cost deltas in STATUS.md.
2. **Phase 2 – Planner and Coordinator Evolution** (bridges 0.1.0 scope)
   - Promote planner outputs to task graphs with coordinator scheduling.
   - Persist ReAct traces for replay and debugging.
   - Document agent responsibilities and tool interfaces.
3. **Phase 3 – Graph-Augmented Retrieval** (extends storage/search roadmap)
   - Build session knowledge graphs, neighbor expansion, and contradiction
     checks.
   - Export graph artifacts and surface policy triggers for contradictions.
4. **Phase 4 – Evaluation Harness and Layered UX** (aligns with QA goals)
   - Automate TruthfulQA, FEVER, and HotpotQA subsets for continuous scoring.
   - Add layered outputs, Socratic prompts, and per-claim audit UX.
5. **Phase 5 – Cost-Aware Model Routing** (feeds performance objectives)
   - Route tasks to heterogeneous models with budget-aware fallbacks.
   - Monitor token, latency, and accuracy telemetry for regression detection.
6. **Phase 6 – Hierarchical Retrieval Integration** (targets 0.1.1 window)
   - Deliver the prototype tree builder, calibration validation suite, and
     dynamic-corpus safeguards before enabling the retriever by default.
   - Instrument traversal depth, path scoring, and fallback telemetry so
     operators can monitor calibration drift.
   - Benchmark against LATTICE’s ≈9 % Recall@100 and ≈5 % nDCG@10 uplift on
     BRIGHT before expanding rollout.
     [LATTICE hierarchical retrieval findings]
     (docs/external_research_papers/arxiv.org/2510.13217v1.md)

Roadmap checkpoints and release notes should reference the phase identifiers
when logging progress or opening follow-up tickets.

## 0.2.0 – API stabilization and improved search

The next minor release focuses on API improvements and search enhancements:

- Complete all search backends with cross-backend ranking and
  embedding-based search (see tasks in CODE_COMPLETE_PLAN lines 38-46).
- Add streaming responses and webhook notifications to the REST API
  (implemented per TASK_PROGRESS lines 143-150).
- Support hybrid keyword/semantic search and a unified ranking algorithm.
- Continue refining the web interface and visualization tools.

## 0.3.0 – Distributed execution and monitoring

Key features planned for this release include:

- Distributed agent execution across processes and storage backends
  (see CODE_COMPLETE_PLAN lines 156-160 and TASK_PROGRESS lines 182-192).
- Coordination mechanisms for distributed agents and parallel search.
- Expanded monitoring including real-time metrics and GPU usage.

## 1.0.0 – Stable interfaces and performance tuning

The 1.0.0 milestone aims for a polished, production-ready system:

- Packaging and deployment planning draw on [prepare-first-alpha-release].
  - Integration stability depends on closing
    [address-storage-setup-concurrency-crash (archived)][address-storage-archived],
    [resolve-resource-tracker-errors-in-verify (archived)][resolve-resource-archived], and
    [resolve-deprecation-warnings-in-tests (archived)][resolve-deprecation-archived].
- Long-term operations rely on keeping the distributed and monitor
  specifications in sync with implementation changes; both docs were reviewed
  on September 17, 2025.

These tasks proceed sequentially: containerization → deployment validation →
performance tuning.

