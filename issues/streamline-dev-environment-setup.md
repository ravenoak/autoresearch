# Streamline dev environment setup

## Context
Running `scripts/setup.sh` attempted to download large GPU-focused packages such as
`torch`, `nvidia-cublas-cu12`, and `nvidia-cudnn-cu12` before installing basic
development tools. These multi-hundred-megabyte downloads make the bootstrap
impractical in constrained environments and prevented completing the install.
A lightweight bootstrap is needed so linting and tests can run without the GPU
dependencies.

## Acceptance Criteria
- Provide a minimal setup path that installs only essential development tools.
- Adjust `uv sync` extras or dependencies to avoid heavy GPU downloads by default.
- Document the lightweight bootstrap in setup instructions.
- Verify the minimal setup supports `flake8`, `mypy`, and the test suite.

## Status
Open
