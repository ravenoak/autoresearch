# Container Images

This directory provides Dockerfiles for building OCI images of Autoresearch with
packaging extras installed. Images exist for Linux, macOS, and Windows.

## Build

```bash
docker build -f docker/Dockerfile.linux -t autoresearch-linux .
docker build -f docker/Dockerfile.macos -t autoresearch-macos .
docker build -f docker/Dockerfile.windows -t autoresearch-windows .
```

## Publish

Tag the images for your registry and push them:

```bash
docker tag autoresearch-linux <registry>/autoresearch:linux
docker push <registry>/autoresearch:linux
```

Repeat for the macOS and Windows tags.

## Packaging

Run the packaging scripts in each container to build distributions.

Linux and macOS:

```bash
docker run --rm -v "$PWD/dist:/dist" autoresearch-linux \
    scripts/package.sh /dist
```

Windows:

```powershell
docker run --rm -v ${PWD}\dist:C:\dist autoresearch-windows \
    powershell -File scripts\package.ps1 -DistDir C:\dist
```
