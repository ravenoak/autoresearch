# Avoid large downloads in task verify

## Context
Running `task verify` pulls GPU extras that download gigabytes of packages such as Torch and NVIDIA CUDA libraries. This slows local development and blocks environments with limited bandwidth.

## Dependencies
None.

## Acceptance Criteria
- `task verify` completes without downloading GPU dependencies by default.
- GPU extras remain available behind an explicit `EXTRAS` flag with prebuilt wheels.
- Documentation explains how to include GPU extras when needed.
- Release docs reflect the reduced default footprint.

## Status
Archived
