### Autoresearch — **Formal Requirements Specification v1.0 (Enhanced & Clarified)**

---

## 1  Scope & Vision

Autoresearch is a **local-first, Python 3.12+** research assistant that performs evidence-driven investigation through a **dialectical, Promise-Theory, multi-agent** architecture. It is modular, extensible, and testable, supporting:

* **CLI** (Typer, primary entry point for all user and automation workflows, with adaptive output)
* **REST API** (FastAPI, future)
* **MCP tool** (`autoresearch.search`)
* All computation and data **remain on the user’s machine**; cloud LLM APIs are optional.
* All storage uses **embedded databases only**—chiefly **DuckDB + vector** and **RDFLib on SQLite/BerkeleyDB**.
* The user can tune how much of the Dynamic Knowledge Graph (DKG) is cached **in-RAM NetworkX vs. lazy-loaded from DuckDB**.
* **Configuration** is centralized, validated, and hot-reloadable.

---

## 2  Functional Requirements

| ID       | Requirement                                                                                                                                      | Priority | Verification Method                        |
| -------- | ------------------------------------------------------------------------------------------------------------------------------------------------ | -------- | ------------------------------------------ |
| **F-01** | Accept natural-language queries via CLI (primary), HTTP `/query`, or MCP tool.                                                                   | Must     | Unit + integration + BDD tests.            |
| **F-02** | Orchestrate ≥ 3 agents (Synthesizer, Contrarian, Fact-Checker) with **rotating Primus** cycle (thesis→antithesis→synthesis).                     | Must     | LangGraph trace; log sequence; BDD.        |
| **F-03** | Retrieve external information (web search, local docs, DKG) **with source metadata** for every claim.                                            | Must     | JSON validator for `sources`.              |
| **F-04** | Persist new claims into **Hybrid DKG**:  ⬩ NetworkX (RAM)  ⬩ DuckDB tables (`nodes`, `edges`, vectors)  ⬩ RDFLib quad-store (SQLite/BerkeleyDB). | Must     | SQL row count increment; RDF quad present. |
| **F-05** | Configurable **iterations** (`loops`) and **agent roster** via TOML; hot-reload on change.                                                       | High     | Watchfiles trigger → new agent visible.    |
| **F-06** | Return **schema-validated JSON** containing `answer`, `citations`, `reasoning`, `metrics` **when requested or piped**; otherwise, output must be readable, well-formatted Markdown or plaintext for humans, with clear dialectical structure. | Must     | Pydantic validation; BDD; manual review.   |
| **F-07** | Expose **Prometheus** metrics (token, latency, error, graph-hit).                                          | High     | Prometheus scrape & Grafana dashboard.     |
| **F-08** | Provide **interactive mode** allowing user or peer-agent input each loop.                                                                        | Should   | Manual QA script; BDD.                     |
| **F-09** | Allow **RAM/Disc tuning**: user sets `ram_budget_mb`; system evicts least-recent graph nodes to DuckDB when exceeded.                            | Should   | Memory profiler; eviction log.             |
| **F-10** | Enable **vector search** on DuckDB (`CREATE INDEX … USING hnsw`) for embeddings; k-NN latency < 150 ms for 10 k vectors.                         | Should   | Benchmark test.                            |
| **F-11** | Support **multiple LLM/search backends** (OpenAI, LM Studio, Anthropic, local) via config. HTTP adapters call each provider's REST API. |
Must     | Unit/integration tests; config reload.     |
| **F-12** | Support **multiple reasoning modes** (direct, dialectical, chain-of-thought, extensible). |
Must     | BDD/unit tests; plugin registration.       |
| **F-14** | All errors and config issues are clear, actionable, and logged.                                                                                  | Must     | Unit/integration tests.                    |
| **F-15** | All modules are testable and covered by unit, integration, and BDD tests.                                                                       | Must     | Coverage report; BDD.                      |
| **F-16** | System is extensible for new backends, reasoning modes, and agent types via config/plugins.                                                      | Must     | Plugin test; config reload.                |
| **F-17** | **CLI output adapts to context**: Markdown/plaintext for humans (TTY), JSON for automation (pipe/flag); dialectical structure is visually distinct for humans and explicit in JSON for machines. | Must | BDD/manual review/unit tests.              |
| **F-18** | **Accessibility**: Output is screen-reader friendly, avoids color-only cues, and is actionable for all users.                                    | Must     | Accessibility review/manual test.          |
| **F-19** | Search local directories. User can select a path to index text and code files. Results must cite the file path and snippet so provenance is clear. | Should   | Unit tests for local file indexing; BDD scenario. |
| **F-20** | Search Git repositories by path. The system scans working tree and commit history, indexing commit messages and diffs. Results return commit hash, file path, and snippet for provenance. | Should   | Unit tests for git repository search; BDD scenario. |
| **F-21** | Maintain local indexes for directories and Git repositories. Indexing occurs at startup or on user command, capturing file contents and commit history for offline queries. | Should   | Unit tests verifying incremental updates; BDD scenario. |

---

## 3  Non-Functional Requirements

| Quality           | Requirement                                                                 |
| ----------------- | --------------------------------------------------------------------------- |
| **Performance**   | Simple fact query ≤ 15 s on 8-core desktop with 7B local model.             |
| **Portability**   | Pure-Python, single `pip install`; no external DB or server.                |
| **Extensibility** | Agents, databases, protocols registered via entry-points; config-driven.    |
| **Observability** | JSON logs (structlog), Prometheus metrics, OpenTelemetry traces.            |
| **Security**      | No outbound HTTP except user-enabled search/LLM; secrets only via env/TOML. |
| **Security (Indexing)** | Local indexing never transmits file contents externally and respects OS permissions. |
| **Licensing**     | All first-party code MIT/AGPL-compatible; closed LLMs optional.             |
| **Usability**     | CLI `--help`, OpenAPI docs, Markdown-formatted answers for humans, JSON for automation. |
| **Accessibility** | Output is readable and actionable for humans by default; dialectical structure is visually distinct and accessible. |
| **Testability**   | 90%+ code coverage, including error paths and output adaptation.             |
| **Performance (Indexing)** | Indexing up to 10k files or commits completes within 2 min; queries from the index respond in under 1 s. |

---

## 4  Configuration & Hot Reload

*Central file*: `autoresearch.toml` (validated, hot-reloadable)  
*Secrets*: Only in `.env` or environment variables, never in logs or output.  
*Output*: CLI auto-detects context (TTY vs. pipe) and adapts output format; user can override with `--output json|markdown|plain`.

---

## 5  Observability & Metrics

* **loguru + structlog** → JSON logs include `msg_id`, `agent`, `lat_ms`, `tokens_in/out`.
* **prometheus_client** metrics: counters for queries and token usage.
* **OpenTelemetry** tracer spans.
* CLI `autoresearch monitor` opens a live TUI (Rich) summarizing CPU/RAM, token spend.

---

## 6  Scientific-Rigor Rules

* Each `claim` node requires ≥ 1 `source` edge or is flagged `confidence < 0.2`.
* Contrarian auto-triggers when two live claims hold `relation=contradicts`.
* Fact-Checker must attach `"verification":"passed|failed|uncertain"` metadata.
* Background cron (`kg_maintainer`) decays confidence λ = 0.98/day.

---

## 7  Outstanding Decisions

| Decision           | Options                      | Recommendation                                                         |
| ------------------ | ---------------------------- | ---------------------------------------------------------------------- |
| RDF backend        | SQLite vs BerkeleyDB         | Use **BerkeleyDB** if available (faster writes); fall back to SQLite.  |
| Vector lib         | DuckDB ext vs FAISS          | Default DuckDB‐vector; expose plugin interface.                        |
| GUI                | Streamlit vs nothing in v0.8 | Defer; CLI/API + Prometheus first.                                     |
| Distributed add-on | Ray vs Dask                  | Prototype Ray transport adapter later; keep single-process by default. |
| Local search tool  | `ripgrep` CLI vs pure Python | Default to **ripgrep** when available for fast indexing; fall back to Python scanning. |
| Licensing          | MIT + “AGPL preferred”       | Tag core MIT; provide AGPL switch for users who need copyleft.         |

---

### Change-Log v1.0 vs v0.9

* Clarified adaptive CLI output and accessibility as core requirements.
* Strengthened usability, testability, and dialectical transparency.
* Added explicit requirement for output adaptation and accessibility.
