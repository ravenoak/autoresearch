# Container Usage

This guide shows how to build and run platform-neutral Autoresearch
container images.

## Build images

Use the helper script to build runtime or development images. Set `OFFLINE=1`
to install from local wheels.

```
docker/build.sh runtime
docker/build.sh dev
```

## Run the CLI

Mount a host directory for data and invoke the CLI.

```
mkdir -p data
docker run --rm -v "$(pwd)/data:/data" \
  autoresearch-runtime search "example query"
```

## Run the API

Expose a port and mount the data volume.

```
docker run --rm -p 8000:8000 -v "$(pwd)/data:/data" \
  autoresearch-runtime uv run uvicorn autoresearch.api:app \
  --host 0.0.0.0 --port 8000
```

Stop the container with `Ctrl+C`.

## Package distributions

Build source and wheel distributions inside the runtime image.

```
scripts/package.sh dist
```

Set `CONTAINER_IMAGE` to use another image such as `autoresearch-dev`.
