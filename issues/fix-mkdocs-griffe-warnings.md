# Fix mkdocs griffe warnings

## Context
`uv run mkdocs build` reports missing type annotations for `llm_adapter` in
`src/autoresearch/agents/registry.py` and `**kwargs` in
`agents/mixins.py` and `agents/prompts.py`. It also warns about confusing
docstring indentation in `src/autoresearch/storage_backends.py`.
These warnings obscure documentation issues.

## Dependencies
None

## Acceptance Criteria
- Parameters noted by griffe have explicit type annotations.
- The docstring in `storage_backends.py` uses consistent indentation.
- `uv run mkdocs build` completes without warnings.

## Status
Open
