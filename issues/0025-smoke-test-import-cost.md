# Issue 25: Smoke test imports heavy dependencies

Running `uv run scripts/smoke_test.py` hangs while importing the `search`
module. The import chain loads `bertopic`, `plotly`, and `narwhals`, which
perform significant initialization and cause the smoke test to stall for
several minutes.

## Context
The smoke test is intended to provide a quick environment check. Heavy
imports defeat this purpose and mirror the unit test hang reported in #23.

## Acceptance Criteria
- Defer or mock heavy imports so the smoke test completes in under a minute.
- Document any optional extras required for the fast path.
- Update setup instructions if additional steps are introduced.

## Status
Open

## Related
- #23
- #24
