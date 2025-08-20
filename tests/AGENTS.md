# Test Guidelines

These instructions apply to files in the `tests/` directory.

## Markers
- Use `slow` for tests that exceed typical runtime or touch external
  services.
- Use `requires_nlp` for tests needing NLP resources; pair with the
  `.[nlp]` extra.
- Use `requires_ui` for tests depending on UI frameworks; pair with the
  `.[ui]` extra.
- Use `requires_vss` for tests needing the DuckDB VSS extension; pair with
  the `.[vss]` extra.
- Use `requires_git` for tests that rely on Git operations; pair with the
  `.[git]` extra.
- Register any new markers in `pytest.ini`.

## Required extras
- Install base development dependencies with `task install` (uses `uv`).
- Include `.[nlp]` when running tests marked `requires_nlp`.
- Include `.[ui]` when running tests marked `requires_ui`.
- Include `.[vss]` when running tests marked `requires_vss`.
- Include `.[git]` when running tests marked `requires_git`.
- Add extras corresponding to any other markers as needed.

## Cleanup expectations
- Remove temporary files and databases such as `kg.duckdb` and
  `rdf_store`.
- Prefer fixtures like `tmp_path` and `monkeypatch` to isolate side
  effects.
- Run `task clean` if tests generate build artifacts.
- When invoking `pytest` directly, prefix the command with `uv run`.
