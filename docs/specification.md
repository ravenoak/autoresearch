# System Specification: Agentic Serper Search (Enhanced & Clarified)

## 1. Architecture

- Modular Python package under `src/autoresearch/`.
- Entry point: `main.py` (CLI, primary interface for all user and automation workflows).
- Configuration: `config.py` (loads from `.env`, environment, or config file).
- Core logic: Provided by `orchestration/orchestrator.py` coordinating the `agents` modules.
- Output formatting: `output_format.py` for adaptive, context-aware output.
- Logging: Centralized, structured, and secure (no secrets).

## 2. Modules

- **config.py**: Loads, validates, and hot-reloads configuration from `.env`, environment, and TOML.
- **main.py**: CLI entry point, parses args, loads config, runs agent, outputs context-adaptive results.
- **api.py**: FastAPI server exposing `/query`, `/query/batch`, streaming, and metrics endpoints.
- **logging_utils.py**: Logging setup and helpers.
- **output_format.py**: Adapts output for human (Markdown/plaintext) or machine (JSON) context.
- **storage.py**: Persistence for search results and knowledge graph.
- **models.py**: Pydantic models for structured data.
- **tracing.py**: OpenTelemetry tracing configuration helpers.
- **orchestration/orchestrator.py**: Coordinates multi-agent cycles.
- **orchestration/state.py**: Tracks query state between agents.
- **orchestration/reasoning.py**: Reasoning mode definitions and strategies.
- **orchestration/metrics.py**: Prometheus metrics collection utilities.
- **resource_monitor.py**: Tracks CPU and memory usage for Prometheus and the CLI monitor.
- **orchestration/phases.py**: Agent execution phases.
- **agents/**: Implementations of Synthesizer, Contrarian, FactChecker, etc.
- **llm/**: Backend adapters for language models.
 - **search/backends/local_file.py**: Parses PDF, DOCX, and text files from
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
  - Modes: `search`, `monitor`, `config`, etc. The `monitor` mode reports CPU and memory usage and can run interactively.
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
  (`local_file`, `local_git`).
- `local_file` recursively indexes directories specified in `[search.local_file]`;
  PDF files are parsed with **pdfminer**, DOCX with **python-docx**, and text
  files directly. Provide a `path` to the directory, an optional list of
  allowed `file_types`, and an `index_strategy` (e.g., `embedding` or `bm25`).
- `local_git` scans repositories configured with `[search.local_git]` using
  `repo_path` to the repository, optional `branches`, `history_depth`, and
  `index_strategy` for incremental or full indexing. Commit messages, diffs,
  and file revisions are stored for search.

Example configuration enabling local sources:

```toml
[search]
backends = ["serper", "local_file", "local_git"]

[search.local_file]
path = "/path/to/docs"
file_types = ["md", "txt"]

[search.local_git]
repo_path = "/path/to/repo"
branches = ["main"]
history_depth = 100
```

These backends register themselves with the `Search` class via the standard
`register_backend` decorator. When enabled in configuration they participate in
the search workflow like any web provider. Indexed documents are persisted
through `storage.py`, so local results are cached, retrieved, and inserted into
the knowledge graph alongside external data.

Local directories are ingested using **ripgrep** when available for fast content extraction. Each file is chunked, embedded, and stored in DuckDB with its path and modification time. On subsequent runs only changed files are re-indexed to keep the index fresh.

Git repositories are processed via **GitPython**. The backend walks the commit history, storing commit metadata and file snapshots so queries can reference the exact revision. Incremental indexing keeps the database in sync with the repository without reprocessing unchanged commits.

Queries against these local indexes leverage DuckDB vector search. Matches return the snippet, file path, and commit hash when applicable so every result is fully attributable.
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
- Prometheus metrics expose gate decisions, debate depth, and audit outcomes.

## 9. Adaptive Orchestration

- **Scout pass:** Draft a quick answer, run focused retrieval, and extract
  uncertainty signals (coverage, conflicts, multi-hop likelihood).
- **Gate policy:** Decide between early exit and dialectical debate using the
  scout signals, policy-sensitive topic detection, and budget guards.
- **Debate stage:** Limit cycles adaptively; ensure the fact checker audits all
  claims before synthesis and citation formatting.
- **Telemetry:** Record gate inputs and outcomes so policies can be tuned with
  offline evaluation.

## 10. Evidence Pipeline 2.0

- Extract claims from drafts and syntheses at sentence granularity.
- Run iterative retrieval with query expansion and snippet re-ranking.
- Score claim support with entailment checks and a self-checking ensemble for
  instability detection.
- Emit per-claim audit records (`supported`, `weak`, `disputed`) containing
  sources, quotes, entailment scores, and reviewer notes.
- Block synthesis on unsupported claims; require hedging or removal before
  completion.

## 11. Planner and Coordinator

- Planner agent produces a structured task graph with sub-questions, tool
  actions, and success criteria (Self-Ask style).
- Coordinator consumes the task graph, schedules specialized agents, and logs
  ReAct traces for replay.
- Each task encodes model preferences, tool requirements, and evidence exit
  criteria so cheaper models can handle low-risk work.
- Planner outputs persist in the query state for observability and debugging.

## 12. Graph-Augmented Retrieval

- Build a session-scoped knowledge graph from retrieved entities and relations
  using existing storage primitives.
- Generate community summaries and neighbor expansions for prompt augmentation.
- Flag contradictions between candidate answers and graph assertions; escalate
  to contrarian review when inconsistencies appear.
- Export graphs as JSON or GraphML artifacts for downstream auditing.

## 13. Evaluation Harness

- Provide CLI entry points to run TruthfulQA, FEVER, and HotpotQA subsets.
- Record KPIs: accuracy, citation coverage, contradiction rate, cost, and
  latency.
- Store benchmark runs in DuckDB or Parquet for longitudinal analysis.
- Support A/B comparisons between gate policies, model routings, and retrieval
  strategies.

## 14. Layered UX and Outputs

- Layered responses: TL;DR, key findings, per-claim audit table, full debate
  trace, and downloadable session bundle.
- Socratic prompts encourage users to clarify scope or request deeper dives.
- CLI and GUI share `--depth` controls and toggles for graph previews and audit
  exports.
- Session bundles include sources, knowledge graph snapshots, planner traces,
  and configuration digests for reproducibility.
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


## 11. Specification coverage

Track algorithm notes for top-level modules.

- [x] `__init__` (docs/algorithms/__init__.md)
- [x] `__main__` (docs/algorithms/__main__.md)
- [x] `a2a_interface` (docs/algorithms/a2a_interface.md)
- [x] `cache` (docs/algorithms/cache.md)
- [x] `cli_backup` (docs/algorithms/cli_backup.md)
- [x] `cli_helpers` (docs/algorithms/cli_helpers.md)
- [x] `cli_utils` (docs/algorithms/cli_utils.md)
- [x] `config_utils` (docs/algorithms/config_utils.md)
- [x] `data_analysis` (docs/algorithms/data_analysis.md)
- [x] `distributed_coordination` (docs/algorithms/distributed_coordination.md)
- [x] `error_recovery` (docs/algorithms/error_recovery.md)
- [x] `error_utils` (docs/algorithms/error_utils.md)
- [x] `errors` (docs/algorithms/errors.md)
- [x] `extensions` (docs/algorithms/extensions.md)
- [x] `interfaces` (docs/algorithms/interfaces.md)
- [x] `kg_reasoning` (docs/algorithms/kg_reasoning.md)
- [x] `logging_utils` (docs/algorithms/logging_utils.md)
- [x] `mcp_interface` (docs/algorithms/mcp_interface.md)
- [x] `models` (docs/algorithms/models.md)
- [x] `output_format` (docs/algorithms/output_format.md)
- [x] `redis_distributed_workflows` (docs/algorithms/distributed_workflows.md)
- [x] `resource_monitor` (docs/algorithms/resource_monitor.md)
- [x] `storage` (docs/algorithms/storage.md)
- [x] `storage_backends` (docs/algorithms/storage_backends.md)
- [x] `storage_backup` (docs/algorithms/storage_backup.md)
- [x] `streamlit_app` (docs/algorithms/streamlit_app.md)
- [x] `streamlit_ui` (docs/algorithms/streamlit_ui.md)
- [x] `synthesis` (docs/algorithms/synthesis.md)
- [x] `test_tools` (docs/algorithms/test_tools.md)
- [x] `tracing` (docs/algorithms/tracing.md)
- [x] `visualization` (docs/algorithms/visualization.md)
