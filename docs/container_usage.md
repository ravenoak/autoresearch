# Container Usage

This guide explains how to build, run, and maintain Autoresearch container images.

## Build

- Run [docker/build_images.sh](../docker/build_images.sh) to build local images
  for Linux, macOS, and Windows.
- Pass extras using an argument, for example:

  ```bash
  bash docker/build_images.sh full,test
  ```

## Run

- Each build produces images tagged `autoresearch-linux-amd64`,
  `autoresearch-macos`, and `autoresearch-windows`.
- To run the Linux image:

  ```bash
  docker run --rm autoresearch-linux-amd64 --help
  ```

## Maintenance

- Push images to GitHub Container Registry with
  [scripts/release_images.sh](../scripts/release_images.sh):

  ```bash
  bash scripts/release_images.sh ghcr.io/OWNER/autoresearch 0.1.0
  ```
- The dispatch-only workflow
  [release-images.yml](../.github/workflows/release-images.yml) runs the same
  script in CI when triggered manually.

