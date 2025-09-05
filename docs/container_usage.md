# Container Usage

Autoresearch ships Dockerfiles for Linux, macOS, and Windows. Each image
installs project extras via a build argument.

## Build

- Use the `EXTRAS` argument to specify optional dependencies, defaulting to
  `full`.
- Replace `podman` with your container engine.

```bash
podman build -f docker/Dockerfile.linux --build-arg EXTRAS=minimal \
    -t autoresearch-linux .
```

Repeat with the macOS and Windows Dockerfiles on their respective hosts.

## Run

Execute the CLI inside a container to confirm the installation:

```bash
podman run --rm autoresearch-linux autoresearch --help
```

## Release

The `scripts/release_images.sh` script builds and pushes all images:

```bash
bash scripts/release_images.sh ghcr.io/OWNER latest
```

Set `CONTAINER_ENGINE` to `podman` when Docker is unavailable.
