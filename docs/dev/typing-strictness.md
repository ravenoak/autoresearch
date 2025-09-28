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

## Strict run snapshot (2025-09-28 16:08 UTC)

- Command: `uv run mypy --strict src tests`.
- Result: 4,122 errors across 511 files (740 checked). Tests dominate the
  totals, but strict diagnostics also flag newer orchestration helpers and
  monitoring utilities.
- Dominant categories observed:
  - Missing annotations in orchestrator helpers and behaviour steps, notably
    [tests/unit/test_orchestrator_helpers.py]
    (../../tests/unit/test_orchestrator_helpers.py) and
    [tests/behavior/steps/api_async_query_steps.py]
    (../../tests/behavior/steps/api_async_query_steps.py), plus related
    fixtures that wrap refactored helper modules.
  - Third-party stub gaps for optional extras (`streamlit`, `ray`, `networkx`,
    `matplotlib`, `duckdb_extension_vss`, `spacy.cli`) despite the vendored
    stubs path, highlighting where additional packages or shim updates are
    still required.
  - HTTP and cache helpers returning `Any` or using incorrect attributes in
    [src/autoresearch/cache.py](../../src/autoresearch/cache.py),
    [src/autoresearch/monitor/system_monitor.py]
    (../../src/autoresearch/monitor/system_monitor.py), and
    [src/autoresearch/llm/pool.py](../../src/autoresearch/llm/pool.py).
  - Graph-backed storage modules such as
    [src/autoresearch/storage_backends.py]
    (../../src/autoresearch/storage_backends.py) and
    [src/autoresearch/storage.py](../../src/autoresearch/storage.py) where
    strict rdflib typing uncovers attribute and return-type mismatches surfaced
    by the new helpers.
- Exclusions: none. The strict preset applies globally, and remaining
  suppressions must be justified inline.

## Representative modules and triage notes

- **Tests (unit, integration, behaviour)** – Thousands of missing annotations
  across orchestrator, API, and CLI suites (see
  [tests/integration/test_monitor_metrics.py]
  (../../tests/integration/test_monitor_metrics.py) and
  [tests/behavior/steps/agent_orchestration_steps.py]
  (../../tests/behavior/steps/agent_orchestration_steps.py)).
  Establishing shared fixtures and helper protocols for the refactored
  behaviour steps will eliminate large swaths of `no-untyped-def` noise.
- **Optional extras and vendored stubs** – Import errors for `streamlit`,
  `ray`, `duckdb_extension_vss`, and `matplotlib` show where additional stub
  packages or expanded files under `typings/` are still required so that
  orchestration helpers and UI modules type-check.
- **Core orchestration utilities** – Recent helper refactors in
  [src/autoresearch/orchestration/utils.py]
  (../../src/autoresearch/orchestration/utils.py),
  [src/autoresearch/orchestration/orchestrator.py]
  (../../src/autoresearch/orchestration/orchestrator.py), and
  [src/autoresearch/orchestration/token_utils.py]
  (../../src/autoresearch/orchestration/token_utils.py) surface `Any` returns,
  redundant casts, and TypedDict misuse that ripple into behaviour-step
  assertions.
- **Monitoring and API layers** – Modules such as
  [src/autoresearch/monitor/metrics.py]
  (../../src/autoresearch/monitor/metrics.py) and
  [src/autoresearch/api/auth.py](../../src/autoresearch/api/auth.py) require
  concrete protocol definitions for Starlette/FastAPI integration, aligning
  them with the orchestrator helpers relied on by the new behaviour suites.

## TYPE_CHECKING usage review

- Files like
  [src/autoresearch/storage_backends.py]
  (../../src/autoresearch/storage_backends.py)
  gate heavy optional imports (e.g., `kuzu`) behind `if TYPE_CHECKING:` blocks.
  This pattern aligns with the preferred approach—runtime availability remains
  optional while type checkers benefit from the annotations. New strict work
  should follow the same structure for optional dependencies.

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
