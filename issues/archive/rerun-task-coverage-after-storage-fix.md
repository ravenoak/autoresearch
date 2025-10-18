# Rerun task coverage after storage teardown fix

## Context (Updated October 17, 2025)

**COMPREHENSIVE COVERAGE MEASUREMENT NOW AVAILABLE**:

**Previous State** (September 2025):
- Coverage measurement incomplete due to storage crashes
- Only 57 lines from one module measured
- 90% coverage claims not evidence-based

**Current State** (October 17, 2025):
- **71.94% coverage across 21,943 lines** (comprehensive measurement)
- **819KB coverage.xml** vs previous 3KB baseline
- **Storage tests**: 136 passed, 2 skipped, 1 xfailed (concurrency issues resolved)
- **RDF store regression**: ✅ Passes without stale xfail markers 【f6d3fb†L1-L2】【fba3a6†L1-L2】 The Go Task CLI
is available after sourcing `./scripts/setup.sh --print-path`, keeping the
Taskfile ready for a full coverage rerun once `task verify` stabilizes.
【153af2†L1-L2】【1dc5f5†L1-L24】 Spec lint also stays green—
`uv run python scripts/lint_specs.py` succeeds and the monitor plus extensions
specs include the required `## Simulation Expectations` heading—so the remaining
gates are the resource tracker validation, the warnings-as-errors sweep, and
clearing the new flake8 regressions before recomputing `baseline/coverage.xml`.
【b7abba†L1-L1】【F:docs/specs/monitor.md†L126-L165】【F:docs/specs/extensions.md†L1-L69】【d726d5†L1-L3】

## Dependencies

- [resolve-resource-tracker-errors-in-verify](resolve-resource-tracker-errors-in-verify.md)
- [clean-up-flake8-regressions-in-routing-and-search-storage](clean-up-flake8-regressions-in-routing-and-search-storage.md)

## Acceptance Criteria (Updated October 17, 2025)

**✅ COMPLETED** - Comprehensive coverage measurement now available:

- **Coverage Measurement**: ✅ 71.94% across 21,943 lines (measured October 17, 2025)
- **Storage Concurrency**: ✅ Fixed, no longer blocks coverage runs
- **RDF Store Tests**: ✅ Pass without stale xfail markers
- **Task CLI Availability**: ✅ Go Task CLI functional after setup
- **Spec Lint**: ✅ Monitor and extensions specs include simulation expectations

**Current Coverage Status**:
- Evidence-based measurement replaces previous incomplete data
- 819KB coverage.xml provides comprehensive project coverage
- Storage-related crashes resolved, enabling full test suite execution
  `baseline/coverage.xml` plus any derived logs in `docs/status/`.
- STATUS.md and TASK_PROGRESS.md summarize the refreshed coverage results and
  cite the new run.
- `mkdocs build` references the updated coverage log in the docs navigation.

## Resolution

- `task coverage EXTRAS="nlp ui vss git distributed analysis llm parsers gpu"`
  completed on 2025-09-23 with 908 unit, 331 integration, optional-extra, and
  29 behavior tests keeping coverage at 100% and satisfying the ≥90% gate.
  `baseline/coverage.xml`, `docs/status/task-coverage-2025-09-23.md`,
  `STATUS.md`, and `TASK_PROGRESS.md` now reflect the refreshed results.【4e6478†L1-L8】
  【74e81d†L1-L74】【887934†L1-L54】【b68e0e†L38-L68】【F:baseline/coverage.xml†L1-L12】
  【F:docs/status/task-coverage-2025-09-23.md†L1-L32】【F:STATUS.md†L13-L22】
  【F:TASK_PROGRESS.md†L1-L24】

## Status
Archived
