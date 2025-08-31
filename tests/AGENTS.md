# Test Guidelines

These instructions apply to files in the `tests/` directory.

## Snapshot
- **Purpose:** validate library behavior.
- **Primary language:** Python.
- **Key outputs:** unit, integration, and behavior tests.

## Setup
- Install base development dependencies with `task install` (uses `uv`).
- When invoking `pytest` directly, prefix commands with `uv run --extra test` to include test extras.
- The behavior suite runs as part of `task verify` and `task coverage`.

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
- Use `requires_distributed` for tests that depend on Redis or Ray; pair with
  the `.[distributed]` extra.
- Use `requires_analysis` for tests needing data analysis libraries; pair with
  the `.[analysis]` extra.
- Use `requires_llm` for tests requiring heavy LLM dependencies; pair with the
  `.[llm]` extra.
- Use `requires_parsers` for tests needing document parsing utilities; pair
  with the `.[parsers]` extra.
- Use `redis` for tests interacting with Redis; pair with `requires_distributed`.
- Use `a2a_mcp` for MCP integration; pair with `requires_distributed`.
- Use `error_recovery` for behavior tests verifying recovery paths.
- Use `reasoning_modes` for behavior tests exploring reasoning strategies.
- Use `user_workflows` for end-to-end user scenarios.
- Combine these markers with `requires_*` markers when scenarios need optional
  extras, e.g. tag Streamlit flows with `requires_ui`.
- Implement steps with existing fixtures such as `bdd_context` or `cli_runner`.
- Register any new markers in `pytest.ini`.
- Include extras corresponding to any other markers as needed.
- Scenarios tagged `error_recovery` or `reasoning_modes` run with the base
  `.[test]` extra; add `[nlp]`, `[ui]`, or `[vss]` only when combining with
  their respective `requires_*` markers.
- Remove temporary files such as `kg.duckdb` and `rdf_store`.
- Prefer fixtures like `tmp_path` and `monkeypatch` to isolate side effects.
- Run `task clean` if tests generate build artifacts.

## Coverage Expectations
- `[nlp]`: cover spaCy-powered NLP paths.
- `[ui]`: exercise Streamlit-based interfaces.
- `[vss]`: exercise DuckDB VSS extension hooks.
- `[git]`: cover Git-backed search utilities.
- `[distributed]`: exercise Redis or Ray orchestration helpers.
- `[analysis]`: cover Polars-powered analytics modules.
- `[llm]`: exercise transformer and DSPy integrations.
- `[parsers]`: cover document parsing helpers such as PDF and DOCX.
- When all extras are installed, `task coverage` must report ≥90% overall.

## Reasoning and Continuous Improvement
- Challenge assumptions about coverage and edge cases when writing tests.
- Capture notable testing strategies in commits and update this file as new
  markers or extras emerge.

## AGENTS.md Compliance
- Scope: `tests/` directory; nested `AGENTS.md` files override these rules.
- This AGENTS.md follows the [AGENTS.md spec](https://gist.github.com).
