# Container Usage

Autoresearch ships a multi-stage Dockerfile targeting Linux, macOS, and
Windows. Each stage installs project extras via a build argument and starts the
`autoresearch` CLI.

## Build

- Use the `EXTRAS` argument to specify optional dependencies, defaulting to
  `full`.
- Replace `podman` with your container engine.

Build and push all platforms:

```bash
bash scripts/release_images.sh ghcr.io/OWNER latest
```

Manual builds for a single platform use Docker Buildx targets:

```bash
podman buildx build --target linux --platform linux/amd64 \
    -t autoresearch-linux .
```

Use `macos` or `windows` with the matching `--platform` value to build other
images.

The `docker/build_images.sh` helper builds Linux images for both `amd64` and
`arm64`:

```bash
bash docker/build_images.sh
```

## Run

Images run the CLI automatically. Pass additional flags to invoke commands:

```bash
podman run --rm autoresearch-linux --version
```

Run CLI or tests offline by disabling network access:

```bash
podman run --rm --network none autoresearch-linux-amd64 --version
podman run --rm --network none autoresearch-linux-amd64 \
    uv run pytest tests/unit/test_cli_help.py::test_cli_help_no_ansi -q
```

## Release

`scripts/release_images.sh` builds Linux (amd64, arm64), macOS, and Windows
images using pinned base digests to ensure reproducibility. Set
`CONTAINER_ENGINE` to `podman` when Docker is unavailable.
