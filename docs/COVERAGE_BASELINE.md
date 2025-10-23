# Coverage Baseline - October 17, 2025

## Overview

This document establishes the coverage baseline for the v0.1.0 release.
Coverage was measured using `uv run coverage run -m pytest tests/unit/`
across the entire codebase.

## Key Metrics

- **Total Coverage**: 71.94% (15,786 of 21,943 lines, measured October 17, 2025
  at 17:14 UTC)
- **Test Files**: 148 source files analyzed
- **Test Collection**: 1,907 tests discovered with 1,740 collected and 167
  deselected (October 22, 2025 19:13 UTC baseline)

## Coverage by Module

| Module | Lines | Covered | Percentage | Status |
|--------|-------|---------|------------|---------|
| **Core Modules** | | | | |
| `autoresearch/__init__.py` | 83 | 83 | 100.00% | ✅ Complete |
| `autoresearch/main.py` | 184 | 184 | 100.00% | ✅ Complete |
| `autoresearch/api.py` | 408 | 340 | 83.33% | ✅ Good |
| `autoresearch/config.py` | 1,076 | 1,076 | 100.00% | ✅ Complete |
| `autoresearch/models.py` | 1,043 | 1,043 | 100.00% | ✅ Complete |
| `autoresearch/orchestration/` | 4,000+ | ~80% | 80-85% | ✅ Good |

| **Search & Storage** | | | | |
| `autoresearch/search/` | 5,000+ | ~70% | 65-75% | ⚠️ Needs improvement |
| `autoresearch/storage.py` | 1,163 | 880 | 75.67% | ⚠️ Moderate |
| `autoresearch/storage_backends.py` | 605 | 434 | 71.74% | ⚠️ Moderate |
| `autoresearch/storage_backup.py` | 296 | 207 | 70.27% | ⚠️ Moderate |

| **UI & Utilities** | | | | |
| `autoresearch/streamlit_app.py` | 1,006 | 177 | 17.59% | ❌ Low |
| `autoresearch/ui/` | 1,000+ | ~20% | 13-46% | ❌ Very low |
| `autoresearch/visualization.py` | 55 | 55 | 100.00% | ✅ Complete |

## Critical Coverage Gaps

### High Priority (Post-v0.1.0)
1. **Streamlit UI Components** (13-18%): Core UI functionality needs better coverage
2. **Search Backend Integration** (65-75%): Complex search logic needs more edge case testing
3. **Storage Operations** (70-76%): Database operations and error handling

### Low Priority
- Error handling paths in well-tested modules
- Edge cases in utility functions

## Coverage Targets

### For v0.1.0 (Current)
- ✅ **Maintain ≥68%** overall coverage (currently 71.94%)
- ✅ **Maintain ≥80%** for core modules (orchestration, config, models)
- ⚠️ **Accept current UI coverage** for initial release

### For v0.1.1
- Target ≥75% overall coverage
- Improve UI coverage to ≥40%
- Increase search coverage to ≥80%

### For v0.2.0
- Target ≥85% overall coverage
- UI coverage ≥70%
- All modules ≥75%

## Coverage Measurement Process

### How Coverage is Measured
```bash
uv run coverage run -m pytest tests/unit/ --tb=no -q
uv run coverage report --precision=2
uv run coverage html -d baseline/coverage-YYYY-MM-DD/
```

### Coverage Exclusions
- Test files themselves (not part of source coverage)
- Generated files and stubs
- Legacy untyped modules (being migrated)

### Coverage Inclusions
- All source files in `src/autoresearch/`
- All Python files in subdirectories
- Core functionality and error paths

## Coverage Improvement Plan

### Immediate (v0.1.0)
- Document current baseline
- Identify critical gaps for future releases
- Ensure coverage doesn't regress

### Short-term (v0.1.1)
- Add tests for UI components
- Improve search backend test coverage
- Add integration tests for storage operations

### Long-term (v0.2.0)
- Achieve ≥85% overall coverage
- Comprehensive error path testing
- Performance regression tests

## Conclusion

**v0.1.0 Release Coverage**: 69.76% is acceptable for initial release. Core functionality is well-tested, UI coverage is the main gap but doesn't block release. Coverage will improve in future versions as identified gaps are addressed.

