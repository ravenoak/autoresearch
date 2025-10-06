# Typing strictness baseline

## Configuration audit

- `[tool.mypy]` in [pyproject.toml](../../pyproject.toml) keeps `strict = true`,
  `warn_unused_configs = true`, and `no_implicit_optional = true` enabled for
  every checked module.  Vendored stubs continue to be discovered through
  `mypy_path = ["typings"]`.
- The repository-wide test override is gone.  `[tool.mypy]` no longer defines
  an `exclude` expression, so the strict run now walks every module under
  `src/` and `tests/`.  Legacy and integration suites that still depend on
  dynamic fixtures carry file-level ``# mypy: ignore-errors`` directives until
  they can be annotated.
- Configuration overrides remain narrowly scoped.  Behaviour fixtures stay at
  `strict = true`, and no package-level `ignore_errors` flags are enabled.

## Test suite expectations

- CI now runs `uv run mypy --strict src tests` as part of `task check` and
  `task verify`.  The command succeeds because fixtures and shared helpers in
  `tests/conftest.py`, `tests/fixtures/`, and `tests/helpers/` are annotated and
  re-export typed protocols from
  [tests/typing_helpers.py](../../tests/typing_helpers.py).
- When a helper returns complex data originating from orchestration state,
  normalise it into a plain `dict[str, Any]` (for example,
  `[dict(claim) for claim in state.claims]`) before handing it to tests.  This
  pattern keeps the test surface covariant while production code continues to
  use `FrozenReasoningStep` internally.
- New fixtures should declare their return type as
  `TypedFixture[T]` (from `tests/typing_helpers.py`) to keep pytest hook
  contracts explicit.

## Strict run snapshot (2025-10-06T04:25:02Z)

- Command: `uv run mypy --strict src tests`
- Result: success with 0 errors across 794 checked files.
- Coverage note: all test suites are included in the strict run.  High-noise
  modules remain quiet because of temporary file-level ``# mypy: ignore-errors``
  markers that document future typing debt.

## Fixture and helper patterns

- Prefer converting orchestration artefacts to concrete dictionaries inside
  fixtures (for example, `return [dict(claim) for claim in selected]`) so test
  helpers work with `Mapping`-agnostic assertions.
- Use `normalize_reasoning_step` when tests must exercise the canonical
  `FrozenReasoningStep` representation; otherwise operate on serialisable
  dictionaries and rely on the production code to re-normalise.
- Treat heavy optional imports the same way production modules do: guard them
  with `if TYPE_CHECKING:` blocks or local protocols rather than module-level
  `type: ignore` comments.

## Next steps

1. Replace the remaining ``# mypy: ignore-errors`` directives with precise
   annotations for behaviour, integration, and performance suites, introducing
   helper protocols when third-party libraries lack stubs.
2. Tighten orchestration and monitoring modules that still pass `Any` between
   layers, now that reasoning payloads expose precise mapping types.
3. Once the suites are typed, remove the temporary ignore markers so that
   `mypy --strict src tests` exercises production and test code without
   suppressing diagnostics.
