# Test Guidelines

These instructions apply to files in the `tests/` directory.

## Snapshot
- **Purpose:** validate library behavior.
- **Primary language:** Python.
- **Key outputs:** unit, integration, and behavior tests.

## Setup
- Install base development dependencies with `task install` (uses `uv`).
- When invoking `pytest` directly, prefix commands with `uv run`.

## Conventions
- Use `slow` for tests that exceed typical runtime or touch external services.
- Use `requires_nlp` for tests needing NLP resources; pair with the `.[nlp]`
  extra.
- Use `requires_ui` for tests depending on UI frameworks; pair with the `.[ui]`
  extra.
- Use `requires_vss` for tests needing the DuckDB VSS extension; pair with the
  `.[vss]` extra.
- Use `requires_git` for tests that rely on Git operations; pair with the
  `.[git]` extra.
- Register any new markers in `pytest.ini`.
- Include extras corresponding to any other markers as needed.
- Remove temporary files such as `kg.duckdb` and `rdf_store`.
- Prefer fixtures like `tmp_path` and `monkeypatch` to isolate side effects.
- Run `task clean` if tests generate build artifacts.

## Reasoning and Continuous Improvement
- Challenge assumptions about coverage and edge cases when writing tests.
- Capture notable testing strategies in commits and update this file as new
  markers or extras emerge.

## AGENTS.md Compliance
- Scope: `tests/` directory; nested `AGENTS.md` files override these rules.
- This AGENTS.md follows the [AGENTS.md spec](https://gist.github.com).
