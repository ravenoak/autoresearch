# Deployment Scenarios

Autoresearch can be deployed in several ways depending on your needs. This guide outlines common approaches.

The project uses **uv** for dependency management. Example commands use `uv`.

## Local Installation

For personal use, run Autoresearch directly on your machine. Install the dependencies and invoke the CLI or API:

```bash
uv venv
uv pip install -e '.[full,parsers,git,llm,dev]'
autoresearch search "example query"
```

Start the API service with Uvicorn for HTTP access:

```bash
uvicorn autoresearch.api:app --reload
```

## Running as a Service

On a dedicated server you can run the API in the background using a process manager such as `systemd` or `supervisord`. Configure environment variables in `.env` and set the working directory to the project root.

## Containerized Deployment (Docker)

Autoresearch can also be containerized. A production `Dockerfile` is included:

```Dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY . /app
RUN pip install uv \
    && uv pip install -e '.[full,parsers,git,llm,dev]'
EXPOSE 8000
CMD ["uvicorn", "autoresearch.api:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run the image:

```bash
docker build -t autoresearch .
docker run -p 8000:8000 autoresearch
```

### Using docker-compose

You can orchestrate the container with `docker-compose`:

```yaml
version: "3.8"
services:
  autoresearch:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
```

Launch with:

```bash
docker compose up --build
```

## Building Wheels for Distribution

Platform-specific wheels can be generated using Go Task:

```bash
task wheels  # builds wheels for Linux, Windows and macOS
```

The wheels will be placed under the `dist/` directory.

## Distributed Deployment

For large-scale workloads you can run Autoresearch on a Ray cluster.  Set
`distributed=true` in your configuration and provide the Ray address in the
`[distributed]` section:

```toml
[distributed]
enabled = true
address = "ray://head-node:10001"
num_cpus = 4
message_broker = "memory"
broker_url = "redis://head-node:6379/0" # optional
```

When started with this configuration, agents are dispatched to remote workers and all
claim persistence is coordinated through a background `StorageCoordinator`.

The coordinator should be started before launching the API or CLI so that every
worker writes to a single DuckDB database. If you specify `message_broker = "redis"`
make sure the Redis service is reachable by all nodes. Result aggregation is
handled by a `ResultAggregator` process which collects agent outputs across
workers.

When `distributed_config.enabled` is set to `true`, the executor waits for the
`StorageCoordinator` to signal readiness before dispatching agents. This
guarantees that claim persistence is available from the first worker cycle. Use
the executor's `shutdown()` method or a graceful termination signal to stop the
coordinator. Queues are drained and closed automatically so no messages are
lost during shutdown.

## Deployment Checks

After starting the service, run the deployment script to validate configuration and perform a health check:

```bash
python scripts/deploy.py
```

To publish a development build to the TestPyPI repository run:

```bash
uv run python scripts/publish_dev.py
```

The script requires the `build` and `twine` packages. Install them with:

```bash
uv pip install build twine
```

Use the `--dry-run` flag to verify the process without uploading:

```bash
uv run python scripts/publish_dev.py --dry-run
```

The packaging commands `uv run python -m build` and
`uv run scripts/publish_dev.py --dry-run` were verified.  See the release notes
for the recorded logs.

If the VSS extension cannot be downloaded because the network is unavailable,
`download_duckdb_extensions.py` loads `.env.offline` and uses the
`VECTOR_EXTENSION_PATH` value so the service starts without vector search
support.

For an actual upload, provide a TestPyPI API token by setting
`TWINE_USERNAME=__token__` and `TWINE_PASSWORD=<token>` before running the
script without `--dry-run`.
## Upgrading
Run `uv pip install -U autoresearch` to refresh an existing installation.
For pip based installs use:
```bash
pip install -U autoresearch
```
Use pip extras to install optional dependencies as needed, for example:
```bash
pip install "autoresearch[full,llm]"
```
Add extras selectively to enable specific features.

### Minimal installation
For lightweight deployments install only the `minimal` extras group:
```bash
pip install "autoresearch[minimal]"
```
Install additional groups later by running `pip install` again with the desired
extras.

## Release workflow

1. Bump the version in `pyproject.toml` and in `autoresearch.__version__`.
2. Regenerate the lock file and install the packaging extras:
   ```bash
   uv lock
   uv pip install -e '.[dev-minimal,build]'
   ```
3. Run the unit and behavior test suites.
4. Build the distribution artifacts:
```bash
uv run python -m build
```
5. Validate the package on TestPyPI without uploading:
   ```bash
   uv run python scripts/publish_dev.py --dry-run
   ```
6. If the metadata looks correct, publish to the TestPyPI repository:
   ```bash
   uv run python scripts/publish_dev.py
   ```
7. If everything looks good, publish to the main PyPI repository:
   ```bash
   uv run twine upload dist/*
   ```

