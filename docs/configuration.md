# Configuration Guide

Autoresearch is configured via `autoresearch.toml` and environment variables in `.env`. This guide provides comprehensive documentation of all configuration options, their default values, valid ranges, and how configuration files are located and loaded.

## Configuration File Locations

Autoresearch searches for configuration files in the following locations, in order:

1. Current working directory (`./autoresearch.toml`)
2. User config directory (`~/.config/autoresearch/autoresearch.toml`)
3. System-wide config directory (`/etc/autoresearch/autoresearch.toml`)

The first file found is used. If no configuration file is found, default values are used.

Environment variables are loaded from `.env` in the current working directory.

## Hot Reload

Changes to configuration files are detected automatically while the tool is running, and the configuration is hot-reloaded without requiring a restart. This applies to both `autoresearch.toml` and `.env` files.

## Configuration Profiles

Autoresearch supports configuration profiles, which allow you to define multiple configurations and switch between them. Profiles are defined in the `[profiles]` section of the configuration file:

```toml
[profiles.offline]
llm_backend = "lmstudio"
vector_extension = false

[profiles.online]
llm_backend = "openai"
vector_extension = true
```

To activate a profile, set the `active_profile` option in the `[core]` section:

```toml
[core]
active_profile = "online"
```

## Environment Variables

All configuration options can be set via environment variables. The naming convention is:

```
SECTION__OPTION=value
```

For example, to set the `llm_backend` option in the `core` section:

```
CORE__LLM_BACKEND=openai
```

For nested options, use additional underscores:

```
STORAGE__DUCKDB__PATH=my_database.duckdb
```

Environment variables take precedence over values in the configuration file.

## CLI Overrides

Several core options can be overridden for a single run using command-line flags:

```bash
autoresearch search --reasoning-mode direct --primus-start 2 "Your question"
```

Available flags:

- `--reasoning-mode` – set the reasoning mode (`direct`, `dialectical`, `chain-of-thought`)
- `--primus-start` – index of the agent to begin the dialectical cycle

## Core Configuration Options

These options are set in the `[core]` section of the configuration file.

| Option | Type | Default | Description | Valid Values |
|--------|------|---------|-------------|-------------|
| `llm_backend` | string | `"lmstudio"` | The LLM adapter to use | `"lmstudio"`, `"openai"`, `"openrouter"`, `"dummy"` |
| `loops` | integer | `2` | Number of reasoning cycles to run | ≥ 1 |
| `ram_budget_mb` | integer | `1024` | Memory budget in megabytes | ≥ 0 |
| `token_budget` | integer | `null` | Maximum tokens allowed per run. When set, the orchestrator adapts this value based on query length, loop count, and parallel group size to avoid wasting tokens. | ≥ 1 or `null` |
| `agents` | list of strings | `["Synthesizer", "Contrarian", "FactChecker"]` | Agents to use in the reasoning process | Any valid agent names |
| `primus_start` | integer | `0` | Index of the starting agent in the agents list | ≥ 0 |
| `reasoning_mode` | string | `"dialectical"` | The reasoning mode to use | `"dialectical"`, `"direct"`, `"chain-of-thought"` |
| `output_format` | string | `null` | Format for output (null = auto-detect) | `null`, `"markdown"`, `"json"`, `"terminal"` |
| `tracing_enabled` | boolean | `false` | Enable OpenTelemetry tracing | `true`, `false` |
| `graph_eviction_policy` | string | `"LRU"` | Policy for evicting items from the knowledge graph | `"LRU"`, `"score"` |
| `default_model` | string | `"gpt-3.5-turbo"` | Default LLM model to use | Any valid model name |
| `active_profile` | string | `null` | Active configuration profile | Any defined profile name |

## Storage Configuration

These options are set in the `[storage.duckdb]` and `[storage.rdf]` sections.

### DuckDB Storage

| Option | Type | Default | Description | Valid Values |
|--------|------|---------|-------------|-------------|
| `path` | string | `"autoresearch.duckdb"` | Path to the DuckDB database file | Any valid file path |
| `vector_extension` | boolean | `true` | Enable vector search extension | `true`, `false` |
| `vector_extension_path` | string | `null` | Path to the VSS extension file (null = auto-download) | `null` or a valid file path |
| `hnsw_m` | integer | `16` | HNSW M parameter for vector index | ≥ 4 |
| `hnsw_ef_construction` | integer | `200` | HNSW ef_construction parameter | ≥ 32 |
| `hnsw_metric` | string | `"l2"` | Distance metric for vector search | `"l2"`, `"ip"`, `"cosine"` |
| `vector_nprobe` | integer | `10` | Number of probes for vector search | ≥ 1 |
| `vector_search_batch_size` | integer | `null` | Batch size for vector search queries | ≥ 1 |
| `vector_search_timeout_ms` | integer | `null` | Query timeout in milliseconds | ≥ 1 |

### RDF Storage

| Option | Type | Default | Description | Valid Values |
|--------|------|---------|-------------|-------------|
| `backend` | string | `"sqlite"` | RDF storage backend | `"sqlite"`, `"berkeleydb"` |
| `path` | string | `"rdf_store"` | Path to the RDF store | Any valid file path |

## Search Configuration

These options are set in the `[search]` section.

| Option | Type | Default | Description | Valid Values |
|--------|------|---------|-------------|-------------|
| `backends` | list of strings | `["serper"]` | Search backends to use | `"serper"`, `"brave"`, `"duckduckgo"` |
| `max_results_per_query` | integer | `5` | Maximum number of results per query | ≥ 1 |
| `hybrid_query` | boolean | `true` | Combine keyword and semantic search | `true`, `false` |
| `use_semantic_similarity` | boolean | `true` | Use semantic similarity for ranking | `true`, `false` |
| `use_bm25` | boolean | `true` | Use BM25 algorithm for ranking | `true`, `false` |
| `semantic_similarity_weight` | float | `0.5` | Weight for semantic similarity | 0.0 to 1.0 |
| `bm25_weight` | float | `0.3` | Weight for BM25 score | 0.0 to 1.0 |
| `source_credibility_weight` | float | `0.2` | Weight for source credibility | 0.0 to 1.0 |
| `use_source_credibility` | boolean | `true` | Use source credibility for ranking | `true`, `false` |
| `domain_authority_factor` | float | `0.6` | Weight for domain authority | 0.0 to 1.0 |
| `citation_count_factor` | float | `0.4` | Weight for citation count | 0.0 to 1.0 |
| `use_feedback` | boolean | `false` | Use user feedback for ranking | `true`, `false` |
| `feedback_weight` | float | `0.3` | Weight for user feedback | 0.0 to 1.0 |

**Note**: `semantic_similarity_weight`, `bm25_weight`, and `source_credibility_weight` must sum to 1.0.

The `semantic_similarity_weight` and `bm25_weight` options let you tune how
semantic embeddings and keyword matches influence the final ranking.
Setting a higher `semantic_similarity_weight` favors embedding-based scores,
while increasing `bm25_weight` prioritizes traditional keyword matching.
When `hybrid_query` is enabled the system automatically mixes keyword
and vector search for each query.

### Search Backends

| Backend | Description | Required Keys |
|---------|-------------|---------------|
| `serper` | Uses the Serper.dev web search API | `api_key` |
| `brave` | Integrates with Brave Search API | `api_key` |
| `duckduckgo` | Queries DuckDuckGo anonymously | _none_ |
| `local_file` | Indexes documents from a directory on disk | `path`, `file_types` |
| `local_git` | Searches a local Git repository's history | `repo_path`, `branches`, `history_depth` |

## Context-Aware Search Configuration

These options are set in the `[search.context_aware]` section.

| Option | Type | Default | Description | Valid Values |
|--------|------|---------|-------------|-------------|
| `enabled` | boolean | `true` | Enable context-aware search | `true`, `false` |
| `use_query_expansion` | boolean | `true` | Expand queries based on context | `true`, `false` |
| `expansion_factor` | float | `0.3` | Controls how many expansion terms to use | 0.0 to 1.0 |
| `use_entity_recognition` | boolean | `true` | Use entity recognition | `true`, `false` |
| `entity_weight` | float | `0.5` | Weight for recognized entities | 0.0 to 1.0 |
| `use_topic_modeling` | boolean | `true` | Use topic modeling | `true`, `false` |
| `num_topics` | integer | `5` | Number of topics to model | 1 to 20 |
| `topic_weight` | float | `0.3` | Weight for topic terms | 0.0 to 1.0 |
| `use_search_history` | boolean | `true` | Use search history for context | `true`, `false` |
| `history_weight` | float | `0.2` | Weight for history terms | 0.0 to 1.0 |
| `max_history_items` | integer | `10` | Maximum number of queries in history | 1 to 100 |

## Agent Configuration

Agent-specific configuration is set in `[agent.<AgentName>]` sections.

| Option | Type | Default | Description | Valid Values |
|--------|------|---------|-------------|-------------|
| `enabled` | boolean | `true` | Enable this agent | `true`, `false` |
| `model` | string | `null` | LLM model to use for this agent (null = use default) | `null` or any valid model name |

Example:

```toml
[agent.Synthesizer]
model = "gpt-4"

[agent.Contrarian]
enabled = true
model = "gpt-3.5-turbo"

[agent.FactChecker]
enabled = true
```

## Complete Example

A complete example configuration is provided in [`examples/autoresearch.toml`](../examples/autoresearch.toml). You can use this as a starting point for your own configuration.

```toml
[search]
backends = ["serper", "local_file", "local_git"]

[search.local_file]
path = "/path/to/research_docs"
file_types = ["md", "pdf", "txt"]

[search.local_git]
repo_path = "/path/to/repo"
branches = ["main"]
history_depth = 50
```

## Tracing

OpenTelemetry tracing is disabled by default. Enable it in `autoresearch.toml`:

```toml
[core]
tracing_enabled = true
```

The same option can be set via the environment variable `CORE__TRACING_ENABLED=true`.

## Distributed Execution

To run agents across multiple processes or machines, configure the `[distributed]` section:

```toml
[distributed]
enabled = true
address = "auto"
num_cpus = 2
```

When enabled, `RayExecutor` dispatches agents to Ray workers for each cycle.

## API Keys

API keys for external services (OpenAI, Serper, Brave Search, etc.) should be set in the `.env` file:

```
OPENAI_API_KEY=sk-...
SERPER_API_KEY=...
BRAVE_SEARCH_API_KEY=...
OPENROUTER_API_KEY=...
```

These keys are automatically loaded and used by the respective adapters.

