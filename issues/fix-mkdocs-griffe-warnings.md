# Fix mkdocs griffe warnings

## Context
`uv run mkdocs build` previously reported missing type annotations for
`llm_adapter` in `src/autoresearch/agents/registry.py` and `**kwargs`
in `agents/mixins.py` and `agents/prompts.py`, along with confusing
docstring indentation in `src/autoresearch/storage_backends.py`. After the
latest dependency sync on 2025-09-15 those `griffe` messages are gone, but the
build now emits warnings about documentation files that are outside the `nav`
configuration and broken relative links such as `specs/api_authentication.md`
from `docs/api_authentication.md`. These warnings still hide actionable doc
regressions and block a clean release build.

## Dependencies
None

## Acceptance Criteria
- Parameters noted by griffe have explicit type annotations.
- The docstring in `storage_backends.py` uses consistent indentation.
- `uv run mkdocs build` completes without warnings.

## Status
Open
