# Deployment Scenarios

Autoresearch can be deployed in several ways depending on your needs. This
guide outlines common approaches.

The project uses **uv** for dependency management. Example commands use `uv`.

## Preflight Checks

Verify configuration before deploying:

- Set `DEPLOY_ENV` and `CONFIG_DIR` to select the configuration set.
- Use an absolute path for `CONFIG_DIR`; relative paths are rejected.
- `deploy.yml` must define a `version` and a non-empty `services` list with
  unique entries.
- Optionally set `EXTRAS` to validate required optional dependencies.
- Set `CONTAINER_ENGINE` to ensure Docker or Podman is available.
- Set `DEPLOY_DIR` to scan other configuration trees.
- Run the validator:

  ```bash
  uv run scripts/validate_deploy.py
  ```

  It scans every `.env` and `*.yml` file under `scripts/deploy/` and reports
  schema violations.

  The validator loads `deploy.yml` and `.env` from `CONFIG_DIR` and exits with
  an error if required keys, services, or files are missing.

Proceed with the deployment steps only after the command exits without
errors.

## Local Installation

For personal use, run Autoresearch directly on your machine. Install the
dependencies and invoke the CLI or API:

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

On a dedicated server you can run the API in the background using a process
manager such as `systemd` or `supervisord`. Configure environment variables in
`.env` and set the working directory to the project root.

## Containerized Deployment (Docker)

Autoresearch provides platform Dockerfiles under `docker/`. The Linux file
supports `linux/amd64` and `linux/arm64` through Docker Buildx.

Build all images locally for verification:

```bash
task docker-build
```

Publish multi-platform images to a registry:

```bash
bash scripts/release_images.sh ghcr.io/OWNER/autoresearch v1.2.3
```

To build a single target manually with Buildx:

```bash
docker buildx build -f docker/Dockerfile.linux \\
  --platform linux/amd64 -t youruser/autoresearch:linux --load .
```

### Maintaining container images

Rebuild images after updating dependencies or base images and push fresh tags
to your registry:

```bash
task docker-build
docker push ghcr.io/OWNER/autoresearch:linux
```

Schedule periodic rebuilds to pick up security patches. Remove unused images
to reclaim disk space:

```bash
docker image prune
```

## Using docker-compose

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

Both `scripts/package.sh` and `scripts/package.ps1` validate that a
configuration file exists before building. Override the default
`pyproject.toml` path by setting `AUTORESEARCH_BUILD_CONFIG`. The scripts also
confirm that the `uv` command is available and exit with an error if it is
missing.

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

When started with this configuration, agents are dispatched to remote workers
and all claim persistence is coordinated through a background
`StorageCoordinator`.

The coordinator should be started before launching the API or CLI so that every
worker writes to a single DuckDB database. If you specify
`message_broker = "redis"` make sure the Redis service is reachable by all
nodes. Result aggregation is handled by a `ResultAggregator` process which
collects agent outputs across workers.

When `distributed_config.enabled` is set to `true`, the executor waits for the
`StorageCoordinator` to signal readiness before dispatching agents. This
guarantees that claim persistence is available from the first worker cycle. Use
the executor's `shutdown()` method or a graceful termination signal to stop the
coordinator. Queues are drained and closed automatically so no messages are
lost during shutdown.

## Configuration Validation

Confirm required settings before starting services.

- Set `DEPLOY_ENV` to the target environment such as `staging` or
  `production`.
- Set `CONFIG_DIR` to the directory containing deployment files; it must exist.
- Ensure `deploy.yml` and `.env` exist in `CONFIG_DIR`.
- Include required entries such as `version` in `deploy.yml` and `KEY` in
  `.env`.
- Optionally set `EXTRAS` to space-separated dependency groups; unknown values
  cause the script to fail fast.
- Optionally set `CONTAINER_ENGINE` to `docker` or `podman` to verify the
  container CLI is available.

Create a configuration directory for each platform such as `config/linux`,
`config/macos`, or `config/windows`. Each directory should contain a
`deploy.yml` and `.env` file. Minimal examples:

```yaml
# deploy.yml
version: 1
services:
  - api
```

```
# .env
KEY=value
```

Run the validation script:

```bash
DEPLOY_ENV=production CONFIG_DIR=config EXTRAS="analysis" \
CONTAINER_ENGINE=docker uv run scripts/validate_deploy.py
```

If any variable, file, or key is missing, the script exits with a non-zero
status and lists the missing items.

Use the platform helpers under `scripts/deploy/` to run the validator and the
deployment helper in one step:

- `bash scripts/deploy/linux.sh`
- `bash scripts/deploy/macos.sh`
- `pwsh scripts/deploy/windows.ps1`

The validator checks schema rules, ensures `services` entries are unique, and
verifies optional extras or container engines when the corresponding
environment variables are set.

### Environment Matrix

The matrix below summarizes common environment configurations:

| DEPLOY_ENV | CONFIG_DIR         |
|------------|-------------------|
| `staging`  | `config/staging`   |
| `production` | `config/production` |

## Deployment Checks

After starting the service, run the deployment script to validate configuration
and perform a health check:

```bash
uv run python scripts/deploy.py
```

The script ensures required settings such as API keys are present. It examines
the active configuration and exits with an error listing any missing variables.
Provide the missing values in your `.env` file or disable the related feature in
`autoresearch.toml`.

Set `AUTORESEARCH_CONFIG_FILE` to point to a custom configuration file. The
deployment script verifies that the file exists before loading settings.

Set `AUTORESEARCH_HEALTHCHECK_URL` to change the endpoint or leave it empty to
skip the check. Example:

```bash
AUTORESEARCH_HEALTHCHECK_URL="" uv run python scripts/deploy.py
```

If validation fails, confirm that the environment variables are spelled
correctly and that the active profile includes the expected backends.

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

