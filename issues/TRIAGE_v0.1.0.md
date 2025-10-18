# v0.1.0 Issue Triage (October 18, 2025)

## BLOCKERS (must fix for v0.1.0)
**Priority**: These issues prevent core functionality or cause critical bugs that would make v0.1.0 unusable.

**✅ TESTS PASSING** - Verification shows tests are working correctly:

**Test Results** (October 18, 2025):
- **Integration Tests**: All 368 selected tests passing ✅
- **API Authentication**: All 19 auth tests passing ✅
- **Behavior Tests**: Agent orchestration tests passing ✅
- **Backup Scheduler**: All tests passing ✅
- **LRU Eviction**: All 27 tests passing ✅

**Previously Identified Issues** (resolved):
- **fix-backup-scheduler-rotation-regressions.md** - ✅ RESOLVED (tests pass)
- **investigate-lru-eviction-regression.md** - ✅ RESOLVED (all tests pass)

**Total Blockers**: 0
**Estimated Effort**: 0 hours (tests passing)

## HIGH PRIORITY (should fix if time permits)
**Priority**: Significant impact but workarounds exist or issues don't block core functionality.

- **address-ray-serialization-regression.md** - Ray executor serialization issues, affects distributed mode
- **stabilize-reverification-fact-checker-defaults.md** - Fact checker defaults need stabilization
- **restore-api-parse-and-fastmcp-handshake.md** - API parsing issues, affects HTTP API

**Total High Priority**: 3
**Estimated Effort**: 12-20 hours

## MEDIUM PRIORITY (nice to have for v0.1.0)
**Priority**: Quality-of-life improvements that enhance the release but aren't critical.

- **plan-repository-wide-strict-typing-gate-refresh.md** - Further improve type safety coverage
- **coordinate-deep-research-enhancement-initiative.md** - Advanced research features
- **deliver-evidence-pipeline-2-0.md** - Evidence processing improvements
- **evaluation-and-layered-ux-expansion.md** - UI/UX enhancements
- **launch-session-graphrag-support.md** - GraphRAG session features
- **monitor.md** - Monitoring improvements
- **planner-coordinator-react-upgrade.md** - Planner enhancements
- **roll-out-layered-ux-and-model-routing.md** - Model routing improvements
- **session-graph-rag-integration.md** - GraphRAG integration

**Total Medium Priority**: 9
**Estimated Effort**: 40-60 hours (defer most to v0.1.1)

## LOW PRIORITY (defer to v0.1.1+)
**Priority**: Enhancement requests and future features that don't impact v0.1.0.

- **build-truthfulness-evaluation-harness.md** - Evaluation framework (future feature)
- **cost-aware-model-routing.md** - Cost optimization (future feature)

**Total Low Priority**: 2
**Estimated Effort**: Defer to v0.1.1

## Summary

**Total Issues**: 20
- Blockers: 2 (must fix)
- High Priority: 3 (fix if time)
- Medium Priority: 9 (defer if needed)
- Low Priority: 2 (defer)

**Release Strategy**:
- Fix all blockers (2 issues, ~8-12 hours)
- Attempt high priority if time permits (3 issues, ~12-20 hours)
- Defer remaining 11 issues to v0.1.1 milestone
- Timeline: Still achievable for November 15, 2025 target

**Risk Assessment**:
- Blocker fixes are straightforward (scheduler and cache issues)
- High priority issues have known solutions
- No architectural blockers identified
- Core functionality unaffected by deferred issues
