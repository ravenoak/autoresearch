# syntax=docker/dockerfile:1

ARG PY_VERSION=3.12

# Linux image
FROM python:${PY_VERSION}-slim AS linux
WORKDIR /app
COPY uv.lock pyproject.toml /app/
RUN pip install --no-cache-dir uv \
    && uv pip sync uv.lock
COPY . /app
CMD ["uv", "run", "uvicorn", "autoresearch.api:app", "--host", "0.0.0.0", "--port", "8000"]

# macOS image (experimental)
FROM python:${PY_VERSION}-slim AS macos
WORKDIR /app
COPY uv.lock pyproject.toml /app/
RUN pip install --no-cache-dir uv \
    && uv pip sync uv.lock
COPY . /app
CMD ["uv", "run", "uvicorn", "autoresearch.api:app", "--host", "0.0.0.0", "--port", "8000"]

# Windows image
FROM mcr.microsoft.com/windows/python:${PY_VERSION} AS windows
WORKDIR /app
COPY uv.lock pyproject.toml /app/
SHELL ["powershell", "-Command", "$ErrorActionPreference = 'Stop';"]
RUN pip install --no-cache-dir uv; \
    uv pip sync uv.lock
COPY . /app
CMD ["uv", "run", "uvicorn", "autoresearch.api:app", "--host", "0.0.0.0", "--port", "8000"]
