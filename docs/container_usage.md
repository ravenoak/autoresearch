# Container Usage

Build and run Autoresearch containers on Linux, macOS, and Windows.

## Build images

Use `scripts/build_images.sh` to create platform images. It targets
Linux (amd64 and arm64), macOS, and Windows. Set `OFFLINE=1` to install
from local wheels or sdists for reproducible builds. Place artifacts in
`wheels/` or generate them with `scripts/package.sh dist`.

```
scripts/build_images.sh
```

To emit OCI archives instead of loading images into Docker:

```
FORMAT=oci scripts/build_images.sh
```

## Run containers

Run the CLI from the Linux image:

```
docker run --rm autoresearch-linux-amd64 --help
```

Mount a host directory for data:

```
mkdir -p data
docker run --rm -v "$(pwd)/data:/data" \
  autoresearch-linux-amd64 search "example query"
```

Expose a port and run the API:

```
docker run --rm -p 8000:8000 -v "$(pwd)/data:/data" \
  autoresearch-linux-amd64 uv run uvicorn autoresearch.api:app \
  --host 0.0.0.0 --port 8000
```

Stop the container with `Ctrl+C`.

## Update containers

Rebuild images after pulling new source code. Re-run the build script
and reload any OCI archives:

```
scripts/build_images.sh
docker load -i dist/autoresearch-linux-amd64.oci
```
