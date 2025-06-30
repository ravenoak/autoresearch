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

## Deployment Checks

After starting the service, run the deployment script to validate configuration and perform a health check:

```bash
poetry run python scripts/deploy.py
```
