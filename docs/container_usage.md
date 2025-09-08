# Container Usage

This guide shows how to build and use Autoresearch container images on Linux,
macOS, and Windows.

## Build images

Run the release script to build multi-architecture images. Use `--push` to
publish to your registry.

```
scripts/release_images.sh --push
```

The script targets `linux/amd64` and `linux/arm64` for the Linux image and uses
the macOS and Windows Dockerfiles for their respective images.

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

