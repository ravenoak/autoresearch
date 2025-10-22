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

- **Tree builders (branching-factor aware):**
  - Implement a bottom-up tree constructor that aggregates child hypotheses
    before promoting summaries, enforcing per-level branching-factor limits.
  - Implement a top-down constructor that expands frontier nodes with
    branching-factor capping and progressive depth pruning.
  - Expose configuration toggles so the orchestrator can swap builders at
    runtime based on query depth, latency budget, and recall goals.
  - Add evaluation harnesses that compare builder throughput and quality on
    staged BRIGHT workloads.
- **Slate constructor (sibling and ℓ-neighbor sampling):**
  - Create a slate assembly module that collects candidate expansions from
    sibling nodes and ℓ-distance neighbors.
  - Implement sampling policies that balance diversity against downstream
    ranker quotas, including deterministic seeds for reproducibility.
  - Validate slate quality with ablations covering sibling-only, ℓ-only, and
    hybrid sampling regimes.
  - Document integration hooks so traversal heuristics can request custom
    sampling weights.
- **Latent score solver (least-squares calibration):**
  - Port the paper's least-squares objective, including regularisation and
    trust-region controls for ill-conditioned batches.
  - Provide utilities that build regression design matrices from traversal
    traces, with hooks for feature normalisation.
  - Add solver diagnostics that surface residual norms and condition numbers to
    telemetry.
  - Cover solver behaviour with unit tests that assert convergence on the
    reference calibration fixtures.
- **Dynamic corpus handling and summary refresh:**
  - Detect corpus mutations via watchers or checkpoints that flag added,
    updated, or deleted artifacts during long-running sessions.
  - Trigger summary rebuild workflows that recompute impacted nodes and update
    derived embeddings.
  - Notify dependent consumers (agents, caches, subscribers) when refreshed
    summaries become available.
  - Record refresh provenance in audit logs, including timestamps and content
    hashes for compliance reviews.

## 13. Acceptance Criteria

- Reproduce the BRIGHT benchmark metrics within a ±1% tolerance using the
  specified hyperparameter grid from the reference study, capturing audit logs
  for every sweep and seed.
- Emit telemetry for calibration residuals and beam throughput at each solver
  invocation, persisting distributions for CI-gated regression checks and
  runbooks.

## 14. Model Staging Requirements

- Stage Gemini 2.5-flash, or an equivalent-capability model, for both offline
  summarisation batches and online traversal inference, preserving deployment
  parity across environments and fallbacks.

