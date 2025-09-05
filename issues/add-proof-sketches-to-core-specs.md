# Add proof sketches to core specs

## Context
The spec linter reports missing `Proof Sketch` sections in `docs/specs/cli-utils.md`,
`docs/specs/api.md`, and `docs/specs/config.md`. The API spec also lacks a top-level
heading. These gaps block specification compliance and cause `task check` to fail.

## Dependencies
None.

## Acceptance Criteria
- Each spec includes a top-level `#` heading and a `## Proof Sketch` section.
- `uv run python scripts/lint_specs.py` passes without missing heading errors.
- `task check` no longer fails due to spec linter warnings.

## Status
Open
