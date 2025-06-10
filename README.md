# Autoresearch

Autoresearch is a local-first research assistant that coordinates multiple agents to
produce evidence-backed answers. It uses a dialectical reasoning process and stores all
data in local databases so that searches and knowledge graphs remain on your machine.
The project is built around a modular Python package located under `src/autoresearch/`.
CLI utilities are provided via Typer and the HTTP API is powered by FastAPI.

## Installation

You can install the project dependencies with either **Poetry** or **pip**.

### Using Poetry
```bash
poetry install
```

### Using pip
```bash
pip install -e .
```

## Quick start

Run a search from the command line:
```bash
autoresearch search "What is quantum computing?"
```

Start the HTTP API with Uvicorn:
```bash
uvicorn autoresearch.api:app --reload
```
Send a request once the server is running:
```bash
curl -X POST http://localhost:8000/query -d '{"query": "explain machine learning"}' -H "Content-Type: application/json"
```

### Configuration hot reload

When you run any CLI command, Autoresearch starts watching `autoresearch.toml`
and `.env` for changes. Updates to these files are picked up automatically and
the configuration is reloaded on the fly. The watcher shuts down gracefully when
the process exits.

For a detailed breakdown of the requirements and architecture, see
[docs/requirements.md](docs/requirements.md) and
[docs/specification.md](docs/specification.md).
