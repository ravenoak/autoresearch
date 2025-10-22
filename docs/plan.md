# Project Expansion Plan: Agentic Serper Search (Enhanced & Clarified)

## 1. Project Structure

- `src/autoresearch/`
  - `__init__.py`
  - `orchestration/orchestrator.py` (core agent coordination)
  - `agents/` (individual agent implementations)
  - `config.py` (configuration system)
  - `main.py` (new entry point)
  - `output_format.py` (adaptive output formatting for CLI)
  - `logging_utils.py` (centralized logging)
  - `agent.py` (agent orchestration, dialectical reasoning)
  - `search.py` (search execution, result processing)
  - `synthesis.py` (answer synthesis logic)
  - `utils.py` (shared helpers/utilities)
- `tests/`
  - Unit, integration, and BDD-style tests
- `docs/`
  - requirements.md, specification.md, requirements_traceability_matrix.md, plan.md
- `.env` (environment variables)
- `autoresearch.toml` (primary config file, hot-reloadable)
- `pyproject.toml`, `README.md`, etc.

## 2. Modularization

- Refactor the monolithic `agentic_serper_search_v2.py` into the modular `orchestration` and `agents` packages:
  - Move configuration, logging, output formatting, and utility functions to separate modules.
  - Isolate agent logic, search logic, and synthesis logic.
- Create `main.py` as the new CLI entry point.
- Ensure all modules are independently testable and extensible.

## 3. Configuration System

- Implement `config.py`:
  - Support `.env`, environment variables, and config files (TOML preferred).
  - Centralize all API keys, model settings, and runtime options.
  - Provide validation, default values, and hot-reload capability.

## 4. Entry Point & CLI

- `main.py`:
  - Parse CLI arguments (Typer).
  - Load configuration.
  - Initialize logging and agent components.
  - Delegate to core logic.
  - **Adaptive output**: Detect context (TTY vs. pipe) and output Markdown/plaintext for humans, JSON for automation; allow explicit override.
  - Provide clear, actionable error messages and help.

## 5. Testing Approach

- **TDD**: Write unit tests for each module and function before implementation.
- **BDD**: Use `pytest-bdd` or `behave` for user-centric scenarios (e.g., "As a user, I want readable dialectical answers").
- Mock external APIs for deterministic tests.
- Target 90%+ code coverage, including error and edge cases.

## 6. Documentation

- Maintain requirements, specification, and traceability matrix.
- Document configuration, usage, extension points, and output formats.
- Provide user and developer guides, including dialectical reasoning explanations.

## 7. CI/CD

- Add linting, formatting, type-checking, and test automation (GitHub Actions or similar).
- Automate release and changelog generation.
- Scan for secrets and dependency vulnerabilities.

## 8. Dialectical Reasoning

- Ensure dialectical reasoning is a first-class feature, with clear separation of thesis, antithesis, and synthesis in outputs and logs.
- For humans, dialectical structure is visually distinct (Markdown sections, headings).
- For machines, dialectical structure is explicit in JSON fields.

## 9. Extensibility

- Design for easy addition of new search backends, reasoning modes, and agent behaviors via plugins/config.
- All extension points are documented and tested.

## 10. Usability & Accessibility

- CLI output is readable and actionable for humans by default.
- Provide Markdown/pretty text for humans, JSON for automation.
- Ensure accessibility (e.g., clear headings, no color-only cues, screen-reader friendly).

## 11. Milestones

1. Refactor and modularize codebase.
2. Implement robust configuration system with validation and hot-reload.
3. Add new entry point and adaptive CLI.
4. Achieve full test coverage (unit, integration, BDD).
5. Complete documentation and traceability.
6. Validate usability and accessibility with real users.
7. Release v1.0.

> **Note:** The CLI is the primary entry point for all user and automation workflows, supporting multiple operational modes and extensibility for future interfaces (REST API, MCP, etc.).
> **Human usability and dialectical transparency are paramount.**

## 12. Deliverables and Subtasks

- **Tree builders:** Implement both bottom-up and top-down tree construction
  strategies with configurable branching-factor limits. Validate switching
  logic so the orchestrator can choose the optimal builder per query depth and
  latency budget.
- **Slate constructor:** Add a slate assembly component that applies
  sibling-based and \(\ell\)-neighbor sampling to diversify candidate
  expansions while respecting downstream ranker constraints.
- **Latent score solver:** Provide a solver that aligns latent traversal scores
  with the paper's least-squares calibration objective, including reusable
  utilities for regression design-matrix generation.
- **Dynamic corpus handling:** Detect corpus mutations during long-running
  sessions and trigger summary refresh workflows that rebuild affected nodes
  and notify dependent consumers.

## 13. Acceptance Criteria

- Demonstrate reproducibility of the BRIGHT benchmark metrics using the
  specified hyperparameter grid from the reference study, including audit logs
  for parameter provenance.
- Emit telemetry for calibration residuals and beam throughput at each solver
  invocation, and confirm thresholds via automated checks in CI.

## 14. Model Staging Requirements

- Stage Gemini 2.5-flash or an equivalent-capability model for offline
  summarisation batches and online traversal inference, ensuring deployment
  parity across environments.

