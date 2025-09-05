# syntax=docker/dockerfile:1

ARG BASE_IMAGE=python:3.12-slim
FROM ${BASE_IMAGE}

WORKDIR /app
COPY uv.lock pyproject.toml /app/
RUN pip install --no-cache-dir uv && uv pip sync uv.lock
COPY . /app
EXPOSE 8000
CMD ["uv", "run", "uvicorn", "autoresearch.api:app", "--host", "0.0.0.0", "--port", "8000"]
