# Container Usage

Autoresearch provides Dockerfiles under `docker/` for Linux, macOS, and
Windows. Images include the project's build extras and are tagged by platform.

## Build

Use the Taskfile to build all images via `docker buildx`:

```bash
task docker-build
```

Each platform can be built on its own:

```bash
task docker-build:linux
task docker-build:macos
task docker-build:windows
```

## Run

Mount your workspace and start a shell inside the container:

```bash
docker run --rm -it -v "$PWD:/workspace" autoresearch:linux bash
```

Replace `autoresearch:linux` with the desired tag. For packaging steps, see
[docker/README.md](../docker/README.md).
