# Baseline workflows

The baseline directory stores archived metrics, coverage references, and
timestamped logs used to track regressions.

## Contributor checklist

- [ ] Run task orchestration through the `uv` launcher: `uv run task verify` and
      `uv run task coverage` should be your default entry points.
- [ ] Capture warning sweeps with `uv run task verify:warnings:log` so new logs
      land under `baseline/logs/` with the UTC timestamp convention.
- [ ] Reinstall extras with `uv run task install` before refreshing baselines to
      ensure the frozen dependencies are in place.
