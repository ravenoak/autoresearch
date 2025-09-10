# Container Images

The `docker/` directory contains Dockerfiles for runtime and development
variants of Autoresearch.

Build an image with the helper script. Set `OFFLINE=1` to install from
local wheels:

```bash
docker/build.sh runtime
```

Use the development variant for testing:

```bash
docker/build.sh dev
```

See `docs/container_usage.md` for usage examples.
