# Address task verify dependency builds

## Context
`task verify` previously stalled while compiling heavy dependencies such as
hdbscan and CUDA packages. Recent runs finish by pulling pre-built wheels, but
GPU libraries are still installed, inflating setup time and size. Further work is
needed to keep the default workflow lightweight for the 0.1.0a1 release.

The **August 31, 2025** `task verify` run pulled pre-built GPU wheels but still
installed them, and the task failed later due to a unit-test deadline rather than
build steps.

## Dependencies

None.

## Acceptance Criteria
- Replace or provide pre-built wheels for heavy packages to avoid lengthy
  builds.
- Update setup and verify tasks to skip GPU-only dependencies by default.
- `task verify` completes in under 15 minutes on a clean environment.

## Status
Open
