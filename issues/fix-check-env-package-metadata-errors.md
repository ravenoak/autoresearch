# Fix check env package metadata errors

## Context
Running `task check` fails because `scripts/check_env.py` reports missing
package metadata for packages such as `GitPython`, `cibuildwheel`,
`duckdb-extension-vss`, `spacy`, and several `types-*` stubs. The script
assumes these dependencies are installed, but minimal environments omit them,
causing the check to exit early.

## Dependencies
None.

## Acceptance Criteria
- Update `scripts/check_env.py` to handle absent packages gracefully or adjust
  installation extras.
- `task check` succeeds in a fresh environment after running `task install`.
- Document any required extras or fallback behavior in `STATUS.md`.

## Status
Open
