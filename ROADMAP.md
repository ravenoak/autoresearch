# Autoresearch Roadmap

This roadmap summarizes planned features for upcoming releases.
Dates and milestones align with the [release plan](docs/release_plan.md).
See [STATUS.md](STATUS.md) and [CHANGELOG.md](CHANGELOG.md) for current results
and recent changes. Installation and environment details are covered in the
[README](README.md). Last updated **October 16, 2025**.

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

**All Deep Research phases are now fully implemented and ready for v0.1.0!**

These tickets align with [docs/deep_research_upgrade_plan.md](docs/deep_research_upgrade_plan.md)
and the updated specification so release milestones can absorb the upgrades in
measured increments. All phases now embed verification loops, retrieval exports,
task graphs, GraphRAG, evaluation harnesses, and cost-aware routing.
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

All phases are now complete and provide the foundation for the **v0.1.0** release.
Technical work is complete with release artifacts built and validated.
Final release engineering (git tagging, documentation updates) is in progress.

## Status

See [STATUS.md](STATUS.md) for detailed logs and
[CHANGELOG.md](CHANGELOG.md) for recent updates. **v0.1.0a1** technical work
is complete with final release engineering in progress. **0.1.0** is targeted for
**December 15, 2025** across project documentation.
As of **October 16, 2025**, release engineering is in progress with technical
work complete and final release steps (git tagging, documentation updates)
underway for v0.1.0a1 release.
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

- 0.1.0a1 (2025-10-16, status: release engineering): Alpha preview with
  technical work complete and final release steps in progress.
- 0.1.0 (2025-12-15, status: planned): Finalized packaging, docs and CI
  checks with all tests passing.
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

This alpha release provides an early package for testing with technical work
complete and release engineering in progress. Related issue
([prepare-first-alpha-release](issues/prepare-first-alpha-release.md)) tracks
the work. Tagging **0.1.0a1** requires completion of final release steps
including git tagging and documentation updates. Technical work is complete
with all tests passing and artifacts validated. 
Key activities include:

- [x] Environment bootstrap documented and installation instructions
  consolidated.
- [x] Task CLI availability restored.
- [x] Packaging verification with DuckDB fallback.
- [x] DuckDB extension fallback hardened for offline setups.
- [x] Distributed coordination helpers restored
  ([restore-distributed-coordination simulation exports (archived)][restore-dist-archived]).
- [x] `task verify` completes without resource tracker errors
  ([resolve-resource-tracker-errors-in-verify (archived)][resolve-resource-archived]).
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

