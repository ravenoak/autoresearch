# Resolve llm extra installation failure

## Context
Attempts to install the `[llm]` extra trigger large CUDA downloads including
`torch` and multiple NVIDIA libraries. The process was terminated before
completion, leaving the environment without required packages. Without the
`llm` extra, `task verify` cannot exercise LLM-dependent tests or reach coverage
targets.

## Dependencies
- [fix-task-verify-coverage-hang](fix-task-verify-coverage-hang.md)

## Acceptance Criteria
- Reduce the size or resource demands of the `[llm]` extra or provide
  CPU-friendly alternatives.
- Ensure `task verify EXTRAS="llm"` installs dependencies within evaluation
  limits.
- Record the resolution in `STATUS.md`.

## Status
Open
