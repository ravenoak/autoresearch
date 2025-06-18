# System Specification: Agentic Serper Search (Enhanced & Clarified)

## 1. Architecture

- Modular Python package under `src/autoresearch/`.
- Entry point: `main.py` (CLI, primary interface for all user and automation workflows).
- Configuration: `config.py` (loads from `.env`, environment, or config file).
- Core logic: Modularized from `agentic_serper_search_v2.py`.
- Output formatting: `output_format.py` for adaptive, context-aware output.
- Logging: Centralized, structured, and secure (no secrets).

## 2. Modules

- **config.py**: Loads, validates, and hot-reloads configuration from `.env`, environment, and TOML.
- **main.py**: CLI entry point, parses args, loads config, runs agent, outputs context-adaptive results.
- **api.py**: FastAPI server exposing query and metrics endpoints.
- **logging_utils.py**: Logging setup and helpers.
- **output_format.py**: Adapts output for human (Markdown/plaintext) or machine (JSON) context.
- **storage.py**: Persistence for search results and knowledge graph.
- **models.py**: Pydantic models for structured data.
- **tracing.py**: OpenTelemetry tracing configuration helpers.
- **orchestration/orchestrator.py**: Coordinates multi-agent cycles.
- **orchestration/state.py**: Tracks query state between agents.
- **orchestration/reasoning.py**: Reasoning mode definitions and strategies.
- **orchestration/metrics.py**: Prometheus metrics collection utilities.
- **orchestration/phases.py**: Agent execution phases.
- **agents/**: Implementations of Synthesizer, Contrarian, FactChecker, etc.
- **llm/**: Backend adapters for language models.
- **search/backends/local_files.py**: Parses PDF, DOCX, and text files from
  user-specified directories for the local search backend.
- **search/backends/local_git.py**: Indexes Git repositories, storing commit
  history and file revisions for search.

## 3. Configuration

- `.env` for secrets and API keys.
- `autoresearch.toml` for structured, hot-reloadable config (agent roster, backend, storage, etc).
- CLI arguments override config file and environment.
- All config is validated (Pydantic or similar).

## 4. CLI

- Command: `autoresearch [MODE] [OPTIONS]`
  - Modes: `search`, `monitor`, `config`, etc.
  - `search`: `autoresearch search [OPTIONS] QUESTION`
- Options for backend, reasoning mode, API keys, model, loops, logging, agent roster, output format, etc.
- **Adaptive output**:
  - By default (TTY), output is readable Markdown or plaintext, with clear sections for thesis, antithesis, synthesis, and citations.
  - If `--output json` or output is piped, output is schema-validated JSON.
  - User can override with `--output` flag.
- Output: Schema-validated JSON with `answer`, `citations`, `reasoning`, `metrics` (for automation); Markdown/pretty text for humans.

## 5. Reasoning Modes

- **Direct**: Single-step answer.
- **Dialectical**: Thesis, antithesis, synthesis (explicitly modeled and logged; visually distinct for humans, explicit fields for machines).
- **Chain-of-thought**: Stepwise reasoning.
- **Extensible**: New modes can be registered via plugins/config.

## 6. Search

- Generate multiple queries per user question or agent prompt.
- Execute queries in parallel (thread pool, rate-limited).
- Truncate/summarize results to fit context window.
- Attach source metadata to every claim.
- Backends include web APIs (Serper, Brave) and local options
  (`local_files`, `local_git`).
- `local_files` recursively indexes directories specified in `autoresearch.toml`;
  PDF files are parsed with **pdfminer**, DOCX with **python-docx**, and text
  files directly. Specify `path` and `file_types` in `[search.local_files]`.
- `local_git` scans repositories configured with `repo_path`, `branches`, and
  `history_depth`, indexing commit messages, diffs, and file revisions.
- Results from all backends are persisted via `storage.py` and inserted into the
  knowledge graph for later reasoning.

## 7. Synthesis

- Use LLM to synthesize answer from search results and reasoning mode.
- Output rationale and answer, with explicit dialectical structure if selected.
- **For humans, dialectical structure is visually distinct (Markdown sections, headings, etc).**
- **For automation, dialectical structure is explicit in JSON fields.**
- Validate output schema (Pydantic).

## 8. Logging & Observability

- Structured logs for all major actions, errors, and reasoning steps (structlog/loguru).
- Log level and output configurable.
- No secrets or sensitive info in logs.
- Prometheus metrics and OpenTelemetry tracing for performance and debugging.

## 9. Testing

- Unit tests for all modules and error paths.
- Integration tests for end-to-end flows.
- BDD scenarios for user stories and dialectical cycles.
- Mocking of external APIs for deterministic tests.
- 90%+ code coverage, including output adaptation.

## 10. Extensibility

- New backends, reasoning modes, and agent types can be added via plugins or config.
- Agent roster and orchestration are config-driven and hot-reloadable.
- All extension points are documented and tested.

> **Note:** The CLI is the main entry point for all user and automation workflows, supporting multiple operational modes and extensibility for future interfaces (REST API, MCP, etc.).  
> **Output must be readable and actionable for humans by default, and dialectically transparent in both human and machine contexts.**
