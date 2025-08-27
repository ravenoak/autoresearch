# Add pdfminer dependency and fix targeted tests

## Context
`task verify` fails during test collection with
`ModuleNotFoundError: No module named 'pdfminer'`. The search module relies on
`pdfminer.six` for PDF text extraction, so targeted tests cannot run and
coverage reports remain incomplete.

## Dependencies
- None

## Acceptance Criteria
- `pdfminer.six` included in development and test dependencies.
- `task verify` runs without missing dependency errors.
- Targeted tests for PDF search scenarios pass.
- Documentation mentions optional PDF support requirements.

## Status
Open
