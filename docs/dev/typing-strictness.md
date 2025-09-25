# Typing strictness baseline

## Configuration audit

- `[tool.mypy]` in [pyproject.toml](../../pyproject.toml) enables
  `ignore_missing_imports = true`, which hides missing stub coverage for
  third-party dependencies rather than surfacing actionable failures.
- The same section disables the `import-untyped` error code, so imports from
  modules without type information quietly become `Any` and propagate through
  the code base. Restoring this diagnostic is required for meaningful strict
  gating.
- `check_untyped_defs = true` is already active, which means re-enabling the
  hidden diagnostics will mostly affect external modules and call sites instead
  of local function bodies.

## Strict run snapshot (2025-09-25 UTC)

- Command: `uv run --extra dev-minimal --extra test mypy --strict src tests`.
- Result: 4,129 errors reported across 531 files (693 checked). The majority
  originate from test suites and helper fixtures, but several core packages
  also fail strict checks.
- Dominant categories observed:
  - Missing function annotations, especially in unit and behaviour tests such
    as [tests/unit/test_ui_save_config.py](../../tests/unit/test_ui_save_config.py)
    and [tests/behavior/steps/api_auth_steps.py](../../tests/behavior/steps/api_auth_steps.py).
  - Untyped decorators (e.g., pytest, behave) that force functions into
    untyped mode, preventing downstream type inference.
  - `Any` leakage from external dependencies, notably `pydantic.BaseModel`
    usages in [src/autoresearch/models.py](../../src/autoresearch/models.py)
    and related agent/message models.
  - Unused `# type: ignore` directives and `no-any-return` violations in
    orchestration helpers such as
    [src/autoresearch/orchestration/utils.py](../../src/autoresearch/orchestration/utils.py)
    and [src/autoresearch/orchestration/token_utils.py](../../src/autoresearch/orchestration/token_utils.py).
  - Attribute export issues surfaced by strict namespace checking, for example
    references to `AgentFactory` from
    [src/autoresearch/orchestration/orchestrator.py](../../src/autoresearch/orchestration/orchestrator.py)
    that are not present in `__all__`.

## Representative modules and triage notes

- **Tests (unit, integration, behaviour)** – Thousands of errors driven by
  missing annotations and untyped pytest/behave decorators. Adding helper
  type aliases and pytest fixtures with explicit return signatures should
  resolve large portions quickly once a consistent convention is agreed upon.
- **Pydantic models** – Every subclass of `BaseModel` is currently typed as
  `Any` because the disabled `import-untyped` diagnostic masks the missing
  stubs. Installing or vendoring Pydantic v1 stubs (or upgrading to a version
  that ships them) is a prerequisite before enabling strict gating on these
  modules.
- **Orchestration utilities** – Several functions return `Any` or rely on
  unchecked dictionaries. These appear more involved because they require
  defining protocol objects and refining return types without breaking
  runtime behaviour.
- **Distributed executors and scripts** – Queue and callable generics lack
  type parameters, and some scripts attempt to monkey-patch methods, which
  strict mypy rejects outright. These likely demand bespoke refactors or
  opt-in `type: ignore[misc]` justifications.

## TYPE_CHECKING usage review

- Files like
  [src/autoresearch/storage_backends.py](../../src/autoresearch/storage_backends.py)
  gate heavy optional imports (e.g., `kuzu`) behind `if TYPE_CHECKING:` blocks.
  This pattern aligns with the preferred approach—runtime availability remains
  optional while type checkers benefit from the annotations. New strict work
  should follow the same structure for optional dependencies.

## Suggested sequencing towards strict gating

1. Restore `import-untyped` diagnostics and audit third-party dependencies for
   missing stubs. Prioritize high-impact packages (Pydantic, DuckDB, rdflib).
2. Establish annotation helpers for pytest/behave fixtures, then roll strict
   mode across `tests/` to prevent regression once coverage improves.
3. Address orchestration utilities and token management helpers by defining
   shared typed interfaces, reducing `Any` returns, and trimming unused
   `type: ignore` directives.
4. Treat complex scripts and distributed components last; evaluate whether the
   functionality should be fully typed, partially ignored with justification,
   or relocated under optional strict modules.
5. Once the above areas stabilize, enable `mypy --strict` in CI, potentially
   with an allowlist that temporarily excludes still-problematic modules while
   the backlog burns down.
