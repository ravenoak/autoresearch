# Deployment Scenarios

Autoresearch can be deployed in several ways depending on your needs. This guide outlines common approaches.

## Local Installation

For personal use, run Autoresearch directly on your machine. Install the dependencies and invoke the CLI or API:

```bash
poetry install --with dev
poetry run autoresearch search "example query"
```

Start the API service with Uvicorn for HTTP access:

```bash
poetry run uvicorn autoresearch.api:app --reload
```

## Running as a Service

On a dedicated server you can run the API in the background using a process manager such as `systemd` or `supervisord`. Configure environment variables in `.env` and set the working directory to the project root.

## Containerized Deployment (Docker)

Autoresearch can also be containerized. A production `Dockerfile` is included:

```Dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir poetry \
    && poetry install --with dev --no-interaction
EXPOSE 8000
CMD ["poetry", "run", "uvicorn", "autoresearch.api:app", "--host", "0.0.0.0", "--port", "8000"]
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
poetry run python scripts/deploy.py
```

To publish a development build to the TestPyPI repository run:

```bash
./scripts/publish_dev.py
```
## Upgrading
Run `poetry update` to refresh an existing installation.
For pip based installs use:
```bash
pip install -U autoresearch
```
Use pip extras to install optional dependencies as needed, for example:
```bash
pip install "autoresearch[full]"
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

1. Bump the version in `pyproject.toml`.
2. Run the unit and behavior test suites.
3. Publish a development build to TestPyPI:

```bash
./scripts/publish_dev.py
```

4. If everything looks good, publish to the main PyPI repository:

```bash
poetry publish --build
```

