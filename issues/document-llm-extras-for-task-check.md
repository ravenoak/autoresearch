# Document LLM extras for task check

## Context
Running `task check` without extras reports missing `dspy-ai` and `fastembed`.
Developers need guidance on when to include the `llm` extra so lint and smoke
tests succeed in environments that exercise LLM features.

## Dependencies
None

## Acceptance Criteria
- Developer docs explain when to invoke `task check EXTRAS="llm"`.
- README notes that `EXTRAS="llm"` satisfies `dspy-ai` and `fastembed`
  requirements for linting.
- CI and local instructions remain dispatch-only.

## Status
Open
