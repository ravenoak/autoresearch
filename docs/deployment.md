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

Autoresearch can also be containerized. A minimal `Dockerfile` might look like:

```Dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY . /app
RUN pip install poetry && poetry install --with dev
CMD ["poetry", "run", "uvicorn", "autoresearch.api:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run the image:

```bash
docker build -t autoresearch .
docker run -p 8000:8000 autoresearch
```

This exposes the API on port 8000 inside the container.
