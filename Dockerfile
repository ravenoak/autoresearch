# syntax=docker/dockerfile:1.4

ARG EXTRAS=full

ARG PYTHON_IMAGE=python:3.12-slim@sha256:
ARG PYTHON_DIGEST=d67a7b66b989ad6b6d6b10d428dcc5e0bfc3e5f88906e67d490c4d3daac57047
FROM ${PYTHON_IMAGE}${PYTHON_DIGEST} AS linux
WORKDIR /workspace
COPY . .
RUN pip install --no-cache-dir uv \
    && uv pip install ".[${EXTRAS}]"
ENTRYPOINT ["autoresearch"]
CMD ["--help"]

ARG MACOS_IMAGE=ghcr.io/cirruslabs/macos-runner:sonoma@sha256:
ARG MACOS_DIGEST=7331fefa25f3e8bca983bea2271ac28b5761a31ce88ea868d477483df9acb50b
FROM ${MACOS_IMAGE}${MACOS_DIGEST} AS macos
ARG EXTRAS
WORKDIR /workspace
COPY . .
RUN /bin/bash -lc "brew update && brew install python@3.12" \
    && pip3 install --no-cache-dir uv \
    && uv pip install ".[${EXTRAS}]"
ENTRYPOINT ["autoresearch"]
CMD ["--help"]

ARG WINDOWS_IMAGE=python:3.12-windowsservercore-ltsc2022@sha256:
ARG WINDOWS_DIGEST=035418c04b5e8fcb13c6b23f6c801a52c510c43e8bf27e2379d26ad8c40c87a7
FROM ${WINDOWS_IMAGE}${WINDOWS_DIGEST} AS windows
ARG EXTRAS
SHELL ["powershell", "-Command", "$ErrorActionPreference = 'Stop';"]
WORKDIR C:/workspace
COPY . .
RUN pip install --no-cache-dir uv; \
    uv pip install ".[$env:EXTRAS]"
ENTRYPOINT ["autoresearch"]
CMD ["--help"]
