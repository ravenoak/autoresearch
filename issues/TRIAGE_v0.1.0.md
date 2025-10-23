# v0.1.0 Issue Triage (October 23, 2025)

## BLOCKERS (must fix for v0.1.0)
**Priority**: These issues prevent core functionality or cause critical bugs
that would make v0.1.0 unusable.

**Evidence snapshot (October 23, 2025 05:41 UTC):**

- `task verify` fails on the cache property Hypothesis flake recorded in
  `baseline/logs/task-verify-20251009T180847Z.log`, so no green suite exists.
- `task coverage` fails on the adaptive rewrite regression captured in
  `baseline/logs/task-coverage-20251009T181039Z.log`, leaving coverage artefacts
  stale at the October 17, 2025 17:14 UTC 71.94 % export (15,786 of 21,943
  lines).
- Pytest collection on October 22, 2025 (19:13 UTC) enumerates 1,907 tests with
  167 deselected, reinforcing that verification still relies on deselection and
  skip markers.

**Active Blockers:**

- Stabilise cache property Hypothesis coverage so `task verify` can complete
  without flaking.
- Repair adaptive rewrite expectations so `task coverage` can finish and refresh
  artefacts.

**Total Blockers**: 2
**Estimated Effort**: 12–18 hours across cache and adaptive rewrite fixes

## HIGH PRIORITY (should fix if time permits)
**Priority**: Significant impact but workarounds exist or issues don't block core functionality.

- **address-ray-serialization-regression.md** - Ray executor serialization issues, affects distributed mode
- **stabilize-reverification-fact-checker-defaults.md** - Fact checker defaults need stabilization
- **restore-api-parse-and-fastmcp-handshake.md** - API parsing issues, affects HTTP API

**Total High Priority**: 3
**Estimated Effort**: 12-20 hours

## MEDIUM PRIORITY (nice to have for v0.1.0)
**Priority**: Quality-of-life improvements that enhance the release but aren't critical.

- **plan-repository-wide-strict-typing-gate-refresh.md** - ✅ COMPLETED - Core typing issues resolved, mypy strict passes
- **coordinate-deep-research-enhancement-initiative.md** - Advanced research features
- **deliver-evidence-pipeline-2-0.md** - Evidence processing improvements
- **evaluation-and-layered-ux-expansion.md** - UI/UX enhancements
- **launch-session-graphrag-support.md** - GraphRAG session features
- **monitor.md** - Monitoring improvements
- **planner-coordinator-react-upgrade.md** - Planner enhancements
- **roll-out-layered-ux-and-model-routing.md** - Model routing improvements
- **session-graph-rag-integration.md** - GraphRAG integration

**Total Medium Priority**: 8 (typing completed)
**Estimated Effort**: 35-50 hours (defer most to v0.1.1)

## LOW PRIORITY (defer to v0.1.1+)
**Priority**: Enhancement requests and future features that don't impact v0.1.0.

- **build-truthfulness-evaluation-harness.md** - Evaluation framework (future feature)
- **cost-aware-model-routing.md** - Cost optimization (future feature)

**Total Low Priority**: 2
**Estimated Effort**: Defer to v0.1.1

## Summary

**Total Issues**: 15
- Blockers: 2 (must fix)
- High Priority: 3 (fix if time)
- Medium Priority: 8 (defer if needed)
- Low Priority: 2 (defer)

**Release Strategy**:
- Stabilise cache and adaptive rewrite blockers (~12-18 hours) before attempting
  any additional scope.
- Attempt high priority items if time permits (3 issues, ~12-20 hours).
- Defer remaining 10 issues to the v0.1.1 milestone.
- Timeline: November 15, 2025 target remains contingent on clearing verify and
  coverage within the next sprint.

**Risk Assessment**:
- Verify/coverage blockers remain outstanding (cache property flake and adaptive
  rewrite regression).
- High priority issues have known solutions but depend on green verify/coverage
  evidence.
- No architectural blockers identified; risk centres on test stability and
  deselection reliance.
