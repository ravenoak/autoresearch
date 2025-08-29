# Fix task verify package metadata errors

## Context
`task verify` fails in the current environment due to missing package metadata for
several optional dependencies (e.g. GitPython, spacy, transformers). The full
test suite cannot run until these packages are available or the task gracefully
handles absent metadata.

## Dependencies

None.

## Acceptance Criteria
- `task verify` installs or resolves all required extras without metadata errors.
- Full test suite runs after `task verify` completes.
- Document the required extras in `docs/installation.md` if steps change.

## Status
Open
