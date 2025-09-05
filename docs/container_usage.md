# Container Usage

Autoresearch ships Dockerfiles for Linux, macOS, and Windows. Each image
installs project extras via a build argument and starts the `autoresearch`
CLI.

## Build

- Use the `EXTRAS` argument to specify optional dependencies, defaulting to
  `full`.
- Replace `podman` with your container engine.

```bash
bash docker/build_images.sh
```

The script builds Linux, macOS, and Windows images. Pass an argument to
override `EXTRAS`.

```bash
podman build -f docker/Dockerfile.linux --build-arg EXTRAS=minimal \
    -t autoresearch-linux .
```

Repeat manual builds with the macOS and Windows Dockerfiles on their
respective hosts when a native build is required.

## Run

Images run the CLI automatically. Pass additional flags to invoke commands:

```bash
podman run --rm autoresearch-linux --version
```

## Release

The `scripts/release_images.sh` script builds and pushes all images:

```bash
bash scripts/release_images.sh ghcr.io/OWNER latest
```

Set `CONTAINER_ENGINE` to `podman` when Docker is unavailable.
