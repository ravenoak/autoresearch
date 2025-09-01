# Address task verify dependency builds

## Context
`task verify` previously stalled while compiling heavy dependencies such as
hdbscan and CUDA packages. References to pre-built wheels now live under
`wheels/gpu`, and setup scripts skip GPU extras unless `AR_SKIP_GPU=0`. The
clean install path keeps the default workflow lightweight and allows
`task verify` to finish in under 15 minutes.

## Dependencies

None.

## Acceptance Criteria
- Replace or provide pre-built wheels for heavy packages to avoid lengthy
  builds.
- Update setup and verify tasks to skip GPU-only dependencies by default.
- `task verify` completes in under 15 minutes on a clean environment.

## Status
Archived
