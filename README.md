# Autoresearch

Autoresearch is a local-first research assistant that coordinates multiple agents to
produce evidence-backed answers. It uses a dialectical reasoning process and stores all
data in local databases so that searches and knowledge graphs remain on your machine.
The project is built around a modular Python package located under `src/autoresearch/`.
CLI utilities are provided via Typer and the HTTP API is powered by FastAPI.

## Roadmap

Autoresearch is currently in the **Development** phase preparing for the
upcoming **0.1.0** release. The codebase already reports version
`0.1.0` in `pyproject.toml`, but that version has **not** been published yet.
The first official release is targeted for **July 20, 2025** once the
documentation and packaging checks complete. See
[docs/release_plan.md](docs/release_plan.md) for the full milestone schedule.

## Installation

Autoresearch requires **Python 3.12 or newer**. You can install the project
dependencies with either **Poetry** or **pip**. See
[docs/installation.md](docs/installation.md) for details on optional features and
upgrade instructions.
The `scripts/setup.sh` helper ensures the lock file is current and installs
all optional extras so development and runtime dependencies are available
for testing.

### Using Poetry
Python 3.12 or newer is required. If multiple Python interpreters exist,
explicitly select version 3.12 with `poetry env use $(which python3.12)`.
Install the development dependencies:
```bash
poetry env use $(which python3)
poetry install --with dev
```

Once installed, verify the environment by running the checks listed under [Running tests](#running-tests).

### Minimal installation
Install only the minimal optional dependencies using pip:
```bash
pip install autoresearch[minimal]
```
When working from a clone, run `scripts/setup.sh` which installs all
development dependencies and optional extras via Poetry.
Use extras to enable additional features, e.g. `pip install "autoresearch[minimal,nlp]"`.
To upgrade a cloned environment run `python scripts/upgrade.py`.

### Using pip
Install the latest release from PyPI:
```bash
pip install autoresearch[core]
```

### Docker
You can run Autoresearch inside Docker using the provided `Dockerfile` and `docker-compose.yml`:

```bash
docker build -t autoresearch .
docker run -p 8000:8000 autoresearch
```

### Building wheels
Use Go Task to create platform-specific wheels:

```bash
task wheels
```
### Upgrading
Use the provided helper to update Autoresearch:
```bash
python scripts/upgrade.py
```
The script runs `poetry update autoresearch` when a `pyproject.toml` is present,
otherwise it falls back to `pip install -U autoresearch`.
Use extras with pip to manage optional dependencies, for example:
```bash
pip install "autoresearch[nlp,ui]"
```


## Quick start

Run a search from the command line:
```bash
autoresearch search "What is quantum computing?"
```

To ensure you are using the latest version you can run:
```bash
python scripts/upgrade.py
```

During processing a progress bar shows the dialectical cycles. Use
`--interactive` to provide feedback after each cycle:

```bash
autoresearch search "Explain AI ethics" --interactive
```
Press `q` at the feedback prompt to abort early.

To visualize the resulting knowledge graph directly in the terminal, use:

```bash
autoresearch search "Explain AI ethics" --visualize
```
This command prints a Rich tree showing the knowledge graph followed by an
ASCII chart of metrics collected during the search.

To save the knowledge graph as an image after running a search, use the
`visualize` subcommand:

```bash
autoresearch visualize "Explain AI ethics" graph.png
```

You can also generate a PNG of the entire RDF store:

```bash
autoresearch visualize-rdf rdf_graph.png
```

Load an ontology and infer relations during a query:

```bash
autoresearch search "Explain AI ethics" --ontology ontology.ttl --ontology-reasoning
```

Use `--ontology-reasoner` to choose a specific reasoning engine.

Start the HTTP API with Uvicorn:
```bash
uvicorn autoresearch.api:app --reload
```
Start the FastMCP server to allow other agents to call Autoresearch as a tool:
```bash
autoresearch serve
```
Then send a request with the helper client:
```python
from autoresearch.mcp_interface import query
print(query("What is quantum computing?")["answer"])
```
Send a query and check collected metrics:
```bash
curl -X POST http://localhost:8000/query -d '{"query": "Explain machine learning"}' -H "Content-Type: application/json"
curl http://localhost:8000/metrics
```

To search your own documents or repositories, enable the `local_file` or
`local_git` backends in `autoresearch.toml`.

## Configuration

Autoresearch uses a TOML configuration file (`autoresearch.toml`) and environment variables (`.env`). A starter configuration is available under [`examples/autoresearch.toml`](examples/autoresearch.toml).

### Core Configuration Options

```toml
[core]
# LLM backend to use (lmstudio, openai, dummy)
llm_backend = "lmstudio"

# Number of reasoning loops to perform
loops = 3
# Maximum token budget per run
token_budget = 4000

# Adaptive token budgeting parameters
adaptive_max_factor = 20
adaptive_min_buffer = 10

# Circuit breaker configuration
circuit_breaker_threshold = 3
circuit_breaker_cooldown = 30

# Enable distributed tracing
tracing_enabled = false

# Reasoning mode: direct, dialectical, chain-of-thought
reasoning_mode = "dialectical"

# Starting agent index for dialectical reasoning
primus_start = 0

# Maximum RAM budget in MB (0 = unlimited)
ram_budget_mb = 1024

# Output format (markdown, json, or null for auto-detect)
output_format = null
```

### Storage Configuration

```toml
[storage.duckdb]
# Path to DuckDB database file
path = "data/research.duckdb"

# Enable vector extension for similarity search
vector_extension = true

# Path to the VSS extension file (optional, auto-detected if not specified)
# vector_extension_path = "./extensions/vss/vss.duckdb_extension"

# HNSW index parameters for vector search
hnsw_m = 16
hnsw_ef_construction = 200
hnsw_metric = "l2"

# For detailed information about DuckDB and VSS extension compatibility,
# see docs/duckdb_compatibility.md

[storage.rdf]
# RDF backend (sqlite, berkeleydb, or memory)
backend = "sqlite"

# Path to RDF store
path = "rdf_store"
# Ontology reasoning engine (owlrl or module:function)
ontology_reasoner = "owlrl"
```

### Agent Configuration

```toml
[agent.Synthesizer]
# Enable or disable the agent
enabled = true

# Model to use for this agent
model = "gpt-3.5-turbo"

[agent.Contrarian]
enabled = true
model = "gpt-4"

[agent.FactChecker]
enabled = true
model = "gpt-3.5-turbo"
```

Additional specialized agents such as `Researcher`, `Critic`, `Summarizer`,
`Planner`, `Moderator`, `DomainSpecialist`, and `UserAgent` can be enabled by
adding corresponding `[agent.AgentName]` sections.

### Search Configuration

```toml
[search]
# Search backends to use
backends = ["serper"]

# Maximum results per query
max_results_per_query = 5
```

Ranking now mixes keyword and semantic similarity. Adjust the weights for
embedding scores, BM25 matching and source credibility in `[search]` to fine
tune the hybrid algorithm.

### Enabling Local File and Git Search

Add the `local_file` or `local_git` backends in `autoresearch.toml` to search
documents on your machine or a Git repository. Results from these backends are
ranked together with web search results:

```toml
[search]
backends = ["serper", "local_file", "local_git"]

[search.local_file]
path = "/path/to/docs"
file_types = ["md", "pdf", "txt"]

[search.local_git]
repo_path = "/path/to/repo"
branches = ["main"]
history_depth = 50
```

Example queries:

```bash
# Search a local directory
autoresearch search "neural networks in notes"

# Search a Git repository
autoresearch search "bug fix commit"
```

### Dynamic Knowledge Graph Settings

```toml
[graph]
# Eviction policy (LRU or score)
eviction_policy = "LRU"

[storage]
# Number of probes for vector search
vector_nprobe = 10
```

### Configuration hot reload

When you run any CLI command, Autoresearch starts watching `autoresearch.toml`
and `.env` for changes. Updates to these files are picked up automatically and
the configuration is reloaded on the fly. The watcher shuts down gracefully when
the process exits.

### Agent Communication Features

Enable message passing and feedback by adding these options to `autoresearch.toml`:

```toml
[coalitions]
research_team = ["Synthesizer", "Contrarian", "FactChecker"]

enable_agent_messages = true
enable_feedback = true
```
Add `research_team` to the `agents` array if you want these members to run
consecutively in each cycle.

Agents can then share short notes with `send_message()` and read them using
`get_messages()` in the next cycle.

## Usage Examples

### Different Reasoning Modes

Autoresearch supports three reasoning modes:

1. **Direct**: Uses only the Synthesizer agent for a straightforward answer
   ```bash
   autoresearch search --reasoning-mode direct "What is quantum computing?"
   ```

2. **Dialectical** (default): Rotates through agents in a thesis→antithesis→synthesis cycle
   ```bash
   autoresearch search --reasoning-mode dialectical "What are the pros and cons of nuclear energy?"
   ```

3. **Chain-of-thought**: Loops the Synthesizer agent for iterative refinement
   ```bash
   autoresearch search --reasoning-mode chain-of-thought "Explain the theory of relativity step by step"
   ```

You can also control which agent starts a dialectical cycle using `--primus-start`:

```bash
autoresearch search --reasoning-mode dialectical --primus-start 1 "How does solar energy work?"
```

Set a custom token budget and number of reasoning loops:

```bash
autoresearch search --loops 3 --token-budget 2000 "Explain AI ethics"
```

Customize circuit breaker settings and adaptive budgeting:

```bash
autoresearch search "Resilient run" --circuit-breaker-threshold 5 --circuit-breaker-cooldown 60 \
  --adaptive-max-factor 25 --adaptive-min-buffer 20
```

### Using Different LLM Backends

```bash
# Using LM Studio (local)
autoresearch search --llm-backend lmstudio "What is machine learning?"

# Using OpenAI
autoresearch search --llm-backend openai "What is machine learning?"
```

### API Usage with Custom Parameters

```bash
# Send a query with custom parameters
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Explain quantum computing",
    "reasoning_mode": "dialectical",
    "loops": 2,
    "agents": ["Synthesizer", "Contrarian"]
  }'
```

Choose specific agents directly from the CLI:

```bash
autoresearch search --agents Synthesizer,Contrarian "What is quantum computing?"
```

### Parallel Query Execution

Run multiple agent groups in parallel for faster results and comparison:

```bash
autoresearch search --parallel \
  --agent-groups "Synthesizer,Contrarian" "FactChecker,Synthesizer" \
  "What are the environmental impacts of cryptocurrency mining?"
```

For a detailed breakdown of the requirements and architecture, see
[docs/requirements.md](docs/requirements.md) and
[docs/specification.md](docs/specification.md).

## Development setup

Install the development dependencies and link the package in editable mode:

```bash
poetry install --with dev
poetry run pip install -e .
```

Alternatively you can run the helper script:

```bash
./scripts/setup.sh
```

The helper installs all dependencies with `poetry install --with dev` and links
the package in editable mode. Tools such as `flake8`, `mypy`, `pytest` and
`tomli_w` are therefore available for development and testing.

## Running tests

Execute all tests once the development environment is ready:

```bash
poetry run flake8 src tests
poetry run mypy src
poetry run pytest -q
poetry run pytest tests/behavior
```

All testing commands should be run through `poetry run` to ensure the correct
virtual environment is used.

Maintain at least 90% test coverage and remove temporary files before submitting a pull request.

### Troubleshooting

- If tests fail with `ModuleNotFoundError`, ensure all dependencies are installed inside the Poetry environment using `poetry install --with dev` or `poetry run pip install -e .`.
- When starting the API with `uvicorn autoresearch.api:app --reload`, install `uvicorn` if the command is not found and verify that port `8000` is free.

## Building the documentation

Install MkDocs and generate the static site:

```bash
poetry run pip install mkdocs
mkdocs build
```

Use `mkdocs serve` to preview the documentation locally.

## Accessibility

CLI output uses Markdown headings and plain-text lists so screen readers can navigate sections. Help messages avoid color-only cues and respect the `NO_COLOR` environment variable for ANSI-free output.
