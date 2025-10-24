# Reduce integration deselection

## Context
Baseline collection runs were deselecting entire optional suites because
`pytest.ini` filtered `requires_ui`, and Taskfile targets expanded that filter to
other extras. Integration tests reported 512 collected / 150 deselected, unit
2345 / 34 deselected, and behavior 315 / 71 deselected during
`uv run --extra test pytest --collect-only` (see chunks 294927, c19b3f, and
39c410). Removing
`requires_ui` from the default mark expression, teaching `tests/conftest.py` to
respect `AR_PYTEST_EXCLUDE`, and simplifying Taskfile filters dropped the counts
to 512 / 145 (chunk d8cf5b), 2345 / 25 (chunk 7a0b07), and 315 / 68 (chunk
689554). Integration deselection now tracks the 145 slow cases explicitly, and
the <10% goal is documented for follow-up trimming of slow scenarios.

## Dependencies
- None

## Acceptance Criteria
- Default pytest runs rely on runtime skip fixtures instead of deselecting
  optional extras.
- `AR_PYTEST_EXCLUDE` can append marker exclusions for bespoke runs.
- Taskfile test targets pass explicit `-m` expressions that align with the pytest
  defaults.
- Deselection metrics are recorded alongside the <10% goal in
  `docs/testing_guidelines.md`.

## Status
Open
