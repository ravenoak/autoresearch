# syntax=docker/dockerfile:1.5

ARG EXTRAS="full,test"
ARG OFFLINE="0"

FROM --platform=$TARGETPLATFORM python:3.12-slim AS linux
WORKDIR /workspace
COPY . .
COPY wheels /wheels
RUN if [ "$OFFLINE" = "1" ]; then \
      pip install --no-index --find-links /wheels uv && \
      uv pip install --no-index --find-links /wheels ".[${EXTRAS}]"; \
    else \
      pip install --no-cache-dir uv && \
      uv pip install ".[${EXTRAS}]"; \
    fi
RUN --network=none autoresearch --help >/dev/null
RUN --network=none uv run pytest \
    tests/unit/test_cli_help.py::test_cli_help_no_ansi -q
ENTRYPOINT ["autoresearch"]
CMD ["--help"]

FROM --platform=linux/amd64 ghcr.io/cirruslabs/macos-runner:sonoma AS macos
ARG EXTRAS
ARG OFFLINE
WORKDIR /workspace
COPY . .
COPY wheels /wheels
RUN /bin/bash -lc "brew update && brew install python@3.12" && \
    if [ "$OFFLINE" = "1" ]; then \
      pip3 install --no-index --find-links /wheels uv && \
      uv pip install --no-index --find-links /wheels ".[${EXTRAS}]"; \
    else \
      pip3 install --no-cache-dir uv && \
      uv pip install ".[${EXTRAS}]"; \
    fi && \
    autoresearch --help >/dev/null && \
    uv run pytest tests/unit/test_cli_help.py::test_cli_help_no_ansi -q
ENTRYPOINT ["autoresearch"]
CMD ["--help"]

FROM --platform=windows/amd64 mcr.microsoft.com/windows/python:3.12 AS windows
ARG EXTRAS
ARG OFFLINE
SHELL ["powershell", "-Command", "$ErrorActionPreference = 'Stop';"]
WORKDIR C:/workspace
COPY . .
COPY wheels C:/wheels
RUN if ($env:OFFLINE -eq '1') { \
        pip install --no-index --find-links C:/wheels uv; \
        uv pip install --no-index --find-links C:/wheels ".[${env:EXTRAS}]"; \
    } else { \
        pip install --no-cache-dir uv; \
        uv pip install ".[${env:EXTRAS}]"; \
    }; \
    autoresearch --help | Out-Null; \
    uv run pytest tests/unit/test_cli_help.py::test_cli_help_no_ansi -q
ENTRYPOINT ["autoresearch"]
CMD ["--help"]
