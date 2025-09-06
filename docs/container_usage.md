# Container Usage

Autoresearch ships Docker and OCI images for Linux, macOS, and Windows.
These images can be built entirely offline when the `wheels/` directory
contains all required wheels.

## Building images

Use the release script to build images locally:

```
./scripts/release_images.sh
```

Set `OFFLINE=1` to install from local wheels during the build:

```
OFFLINE=1 ./scripts/release_images.sh
```

## Running with docker compose

`docker-compose.yml` builds the Linux image and starts a Redis service.

```
docker compose build
docker compose up
```

For offline runs provide the offline environment file:

```
ENV_FILE=.env.offline OFFLINE=1 docker compose build
ENV_FILE=.env.offline docker compose up
```

The API is available at <http://localhost:8000> when the stack is running.
