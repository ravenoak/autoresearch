# Typing strictness baseline

## Configuration audit

- `[tool.mypy]` in [pyproject.toml](../../pyproject.toml) now enables
  `strict = true`, activating the full strict preset for every checked module.
- `warn_unused_configs = true` is set explicitly, so unused sections or typoed
  options fail fast instead of silently drifting out of sync with tooling.
- `no_implicit_optional = true` requires all optional parameters to be written
  as `Optional[T] | None`, which keeps orchestration helpers and behaviour
  steps honest about nullable values.
- `mypy_path = ["typings"]` ensures vendored stubs (for example
  [typings/rdflib](../../typings/rdflib/__init__.pyi)) are discovered alongside
  newly added helper shims.
- There are no `ignore_missing_imports` toggles or per-package allowlists, so
  missing stubs for optional extras surface directly in strict runs.
- A single `tests.*` override keeps the suite runnable under strict mode by
  enumerating the exact error codes currently suppressed (e.g. `no-any-return`,
  `union-attr`, `typeddict-item`). Each code in
  [pyproject.toml](../../pyproject.toml) must be burned down or justified with
  inline ignores before new suppressions are added.

## Test suite expectations

- Every test module is expected to pass under `mypy --strict src tests`, the
  same command wired into [`task check`](../../Taskfile.yml) and
  [`task verify`](../../Taskfile.yml). The broad `ignore_errors = true`
  overrides once applied to `tests.integration.*`, `tests.targeted.*`, and
  archived behaviour suites have been removed. New suppressions must be
  justified inline or with precise module-specific overrides that keep the
  strict gate meaningful.

## Strict run snapshot (2025-09-29 02:23 UTC)

- Command: `uv run --extra dev-minimal --extra test mypy --strict`
  `src/autoresearch/orchestration src/autoresearch/storage.py`
  `tests/unit tests/integration`.
- Result: 2,434 errors across 346 files (423 checked). Freshly typed helpers
  in [tests/typing_helpers.py](../../tests/typing_helpers.py),
  [tests/unit/test_orchestrator_helpers.py]
  (../../tests/unit/test_orchestrator_helpers.py), and
  [tests/integration/test_monitor_metrics.py]
  (../../tests/integration/test_monitor_metrics.py) now pass strict checks, but
  storage and behaviour suites remain the dominant sources of noise.
- Dominant categories observed:
  - Thousands of lingering `no-untyped-def` violations in behaviour, API, and
    distributed orchestration tests such as
    [tests/integration/test_api_auth.py]
    (../../tests/integration/test_api_auth.py) and
    [tests/unit/test_reasoning_modes.py]
    (../../tests/unit/test_reasoning_modes.py).
  - Missing third-party stubs for extras like `dspy`, `PIL`, and `fastmcp`
    despite the newly vendored shims for
    [typings/streamlit](../../typings/streamlit/__init__.pyi),
    [typings/ray](../../typings/ray/__init__.pyi),
    [typings/networkx](../../typings/networkx/__init__.pyi), and
    [typings/duckdb_extension_vss]
    (../../typings/duckdb_extension_vss/__init__.pyi).
  - NetworkX and rdflib integration in
    [src/autoresearch/storage.py](../../src/autoresearch/storage.py) still
    assumes mutable node views and graph methods (`close`, `store`) that strict
    typing flags as missing or misused.
  - Token metrics coercion in
    [src/autoresearch/orchestration/metrics.py]
    (../../src/autoresearch/orchestration/metrics.py) continues to cast nested
    dictionaries to `float`, yielding `arg-type` failures under strict mode.
- Exclusions: none. The strict preset applies globally, and remaining
  suppressions must be justified inline.

## Representative modules and triage notes

- **Tests (unit, integration, behaviour)** – Typed fixtures and helper
  protocols now live in
  [tests/typing_helpers.py](../../tests/typing_helpers.py), giving orchestrator
  helpers deterministic types. The remaining backlog clusters around behaviour
  suites and distributed orchestration tests that still rely on untyped
  factories.
- **Optional extras and vendored stubs** – Newly vendored shims for Ray,
  Streamlit, NetworkX, and the DuckDB VSS extension unblock strict checking in
  CLI tests, but gaps remain for `dspy`, `PIL`, and `fastmcp`. Additional stub
  updates are required before enabling strict checks for the behaviour suite.
- **Core orchestration utilities** –
  [src/autoresearch/orchestration/utils.py]
  (../../src/autoresearch/orchestration/utils.py) and
  [src/autoresearch/orchestration/token_utils.py]
  (../../src/autoresearch/orchestration/token_utils.py) now expose typed data
  classes and protocols, yet downstream call sites (notably
  [src/autoresearch/orchestration/metrics.py]
  (../../src/autoresearch/orchestration/metrics.py)) still rely on `Any`
  conversions that must be tightened.
- **Monitoring and API layers** –
  [tests/integration/test_monitor_metrics.py]
  (../../tests/integration/test_monitor_metrics.py) now executes under strict
  typing, but broader FastAPI and CLI suites await typed fixtures and response
  protocols before we can reduce their `attr-defined` and `no-untyped-def`
  noise.

## TYPE_CHECKING usage review

- Files like
  [src/autoresearch/storage_backends.py]
  (../../src/autoresearch/storage_backends.py)
  gate heavy optional imports (e.g., `kuzu`) behind `if TYPE_CHECKING:` blocks.
  This pattern aligns with the preferred approach—runtime availability remains
  optional while type checkers benefit from the annotations. New strict work
  should follow the same structure for optional dependencies.
- [src/autoresearch/data_analysis.py]
  (../../src/autoresearch/data_analysis.py) and
  [src/autoresearch/kg_reasoning.py]
  (../../src/autoresearch/kg_reasoning.py) now use lightweight protocols to
  represent optional extras. Follow the same pattern—define sentinel classes or
  protocols instead of `type: ignore` when guarding imports.

## Suggested sequencing towards strict gating

1. Harden shared pytest and behave helpers so orchestrator, API, and CLI tests
   pick up consistent typed fixtures, shrinking the strict error surface.
2. Extend vendored stubs (or add dependencies) for high-noise extras such as
   `streamlit`, `ray`, `networkx`, and `duckdb_extension_vss`, mirroring the
   new helper modules they exercise.
3. Refine orchestration and storage helpers—introduce typed protocols for
   cache, HTTP, and rdflib adapters to replace `Any` flows and redundant casts.
4. Tackle monitoring and FastAPI integrations next, ensuring ASGI request and
   response wrappers expose the attributes the behaviour steps assert on.
5. When the above areas stabilize, wire `uv run mypy --strict src tests` into
   CI without excludes, treating any future suppressions as temporary and
   documented inline.
