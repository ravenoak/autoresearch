# Container Usage

This guide shows how to build and use Autoresearch container images on Linux,
macOS, and Windows.

## Build images

Go Task builds all platform images. Set `EXTRAS` to choose optional extras and
`OFFLINE=1` to install from local wheels. Set `CONTAINER_ENGINE=podman` to use
Podman instead of Docker:

```
EXTRAS=analysis OFFLINE=1 task docker-build
```

Images are loaded into the local engine. Set `FORMAT=oci` to emit OCI archives
in `dist/` instead.

## Package distributions

Create source and wheel distributions inside a container by invoking the
packaging script from the host. It launches the `autoresearch-linux` image by
default.

```
scripts/package.sh dist
```

For Windows artifacts use PowerShell.

```
scripts\package.ps1 -DistDir dist
```

Set `CONTAINER_IMAGE` to select a different image such as
`autoresearch-macos`. Generated files appear in the directory supplied on the
host.

## Validate images

Run a basic command in each image to confirm it starts correctly.

- Linux:

  ```
  docker run --rm autoresearch-linux-amd64 --version
  ```

- macOS:

  ```
  docker run --rm autoresearch-macos --version
  ```

- Windows (PowerShell):

  ```
  docker run --rm autoresearch-windows --version
  ```

If you built OCI archives, load them before running the checks:

```
docker load < dist/autoresearch-linux-amd64.oci
```

