# Address task verify dependency builds

## Context
`task verify` previously stalled while compiling heavy dependencies such as
hdbscan and CUDA packages. Pre-built wheels now satisfy these dependencies, and
GPU libraries are skipped by default, keeping the workflow lightweight.

## Dependencies

None.

## Acceptance Criteria
- Provide pre-built wheels for heavy packages to avoid lengthy builds.
- Skip GPU-only dependencies by default.
- `task verify` completes in under 15 minutes on a clean environment.

## Status
Archived
