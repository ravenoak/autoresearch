# Container Usage

This guide shows how to build and use Autoresearch container images on Linux,
macOS, and Windows.

## Build images

Use `scripts/build_images.sh` to build images for Linux, macOS, and Windows.
The first argument selects optional extras. Set `FORMAT=oci` to emit OCI
archives in `dist/` or leave unset to load images into the local engine.

```
FORMAT=oci scripts/build_images.sh analysis
```

Set `CONTAINER_ENGINE=podman` to build with Podman and `OFFLINE=1` to
install from local wheels.

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

