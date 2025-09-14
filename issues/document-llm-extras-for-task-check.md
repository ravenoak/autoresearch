# Document LLM extras for task check

## Context
`task check` fails on September 14, 2025 because `scripts/check_env.py` reports missing
`dspy-ai` and `fastembed` when no extras are specified. Running the command with
`EXTRAS="llm"` installs these dependencies and passes.

## Dependencies
None

## Acceptance Criteria
- `task check` succeeds without manual dependency installation or clearly documents that
  `EXTRAS="llm"` must be set.
- `scripts/check_env.py` reflects the required extras or relaxes checks when LLM features
  are unused.
- Documentation explains how to run `task check` with LLM extras.

## Status
Open
