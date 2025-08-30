# Address task verify dependency builds

## Context
`task verify` stalls when building heavy dependencies such as hdbscan and CUDA
packages during `scripts/setup.sh`. This prevents the full test suite from
running and delays the 0.1.0a1 release.

## Dependencies

None.

## Acceptance Criteria
- Replace or provide pre-built wheels for heavy packages to avoid lengthy
  builds.
- Update setup and verify tasks to skip GPU-only dependencies by default.
- `task verify` completes in under 15 minutes on a clean environment.

## Status
Open
