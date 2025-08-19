# Test Guidelines

These instructions apply to files in the `tests/` directory.

## Markers
- Use `slow` for tests that exceed typical runtime or touch external
  services.
- Use `requires_nlp` for tests needing NLP resources; pair with the
  `.[nlp]` extra.
- Use `requires_ui` for tests depending on UI frameworks.
- Register any new markers in `pytest.ini`.

## Required extras
- Install base dev dependencies as described in the repository root `AGENTS.md`.
- Include `.[nlp]` when running tests marked `requires_nlp`.
- Add extras corresponding to any other markers as needed.

## Cleanup expectations
- Remove temporary files and databases such as `kg.duckdb` and
  `rdf_store`.
- Prefer fixtures like `tmp_path` and `monkeypatch` to isolate side
  effects.
- Run `task clean` if tests generate build artifacts.
