# Stage 0.1.0a1 release artifacts

## Context
`docs/release_plan.md` and `CHANGELOG.md` both outline the path to the
first alpha tag, yet we still need a focused effort that synthesises the
packaging, documentation, and verification outputs into releasable
artifacts. The September 23 baselines confirm `task verify`,
`task coverage`, and warnings-as-errors sweeps succeed, but the lack of a
recent `uv build` dry run and the absence of draft release notes leave a
tangible gap before we can create the `v0.1.0a1` tag.

`issues/prepare-first-alpha-release.md` tracks the overall coordination;
this ticket isolates the concrete PR-sized work: run the packaging
pipeline under `uv`, capture hashes, update the changelog with a drafted
release entry, and sync documentation pointers. From a dialectical point
of view we must weigh the risk of stale metadata against the effort of
rerunning expensive builds. The Socratic step asks whether our existing
baselines truly guarantee installability without this staging sweep.

## Dependencies
- [retire-stale-xfail-markers-in-unit-suite.md]
  (retire-stale-xfail-markers-in-unit-suite.md)
- [prepare-first-alpha-release.md](prepare-first-alpha-release.md)

## Acceptance Criteria
- Execute `uv run python -m build` and
  `uv run scripts/publish_dev.py --dry-run --repository testpypi` in a
  clean environment, saving logs under `baseline/logs/` with timestamps.
- Update `CHANGELOG.md` with a drafted `0.1.0a1` section covering staged
  artifacts, citing the packaging logs.
- Record the dry-run commands, checksums, and resulting wheel tree in
  `docs/release_plan.md` under "Prerequisites for tagging 0.1.0a1".
- Document any environment adjustments, such as `TASK_INSTALL_DIR`, in
  `STATUS.md` so future releases can replicate the setup.
- Ensure `mkdocs.yml` navigation references the updated release notes if
  new sections are added.
- Attach the packaging log paths and resulting artifact hashes to the
  issue comment thread when closing.

## Status
Open
