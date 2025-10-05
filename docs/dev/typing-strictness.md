# Typing strictness baseline

## Configuration audit

- `[tool.mypy]` in [pyproject.toml](../../pyproject.toml) keeps `strict = true`,
  `warn_unused_configs = true`, and `no_implicit_optional = true` enabled for
  every checked module.  Vendored stubs continue to be discovered through
  `mypy_path = ["typings"]`.
- The repository-wide test override is gone.  Instead, the
  `exclude` expression limits the strict run to fixtures and helpers while
  skipping high-noise directories such as `tests/analysis`,
  `tests/behavior/archive`, `tests/behavior/steps`, `tests/performance`, and
  similar targeted suites that still rely on untyped third-party integrations.
- No modules receive `ignore_errors` or broad error-code disables.  The only
  remaining override keeps behaviour helper modules
  ([pyproject.toml](../../pyproject.toml)) pinned to `strict = true`, ensuring
  BDD fixtures stay typed without muting failures elsewhere.

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

## Strict run snapshot (2025-10-05T15:43:40Z)

- Command: `uv run mypy --strict src tests`
- Result: success with 0 errors across 205 checked files.
- Exclusions: `tests/(analysis|benchmark|behavior/(archive|steps)|cli|data|
  evaluation|evidence|integration|performance|targeted|ui|unit)/`.  These
  suites remain on the TODO list below until their fixtures and third-party
  shims are typed.

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

1. Bring the excluded behaviour, performance, and integration suites under
   strict checks by extending fixtures with typed adapters and adding missing
   third-party stubs.
2. Tighten orchestration and monitoring modules that still pass `Any` between
   layers, now that reasoning payloads expose precise mapping types.
3. Replace the temporary test exclusions with module-specific overrides once
   the remaining suites are annotated, keeping `mypy --strict src tests` as the
   default gate for CI.
