# Release Plan

This document outlines the upcoming release milestones for **Autoresearch**.
Dates are aspirational and may shift as development progresses.
The publishing workflow follows the steps in
[deployment.md](deployment.md). Detailed release commands are documented in
[releasing.md](releasing.md). See
[installation.md](installation.md) for environment setup and
ROADMAP.md for high-level milestones.

The project kicked off in **May 2025** (see the initial commit dated
`2025-05-18`). This schedule was last updated on **September 17, 2025** and
reflects that the codebase currently sits at the **unreleased 0.1.0a1** version
defined in `autoresearch.__version__`. The project targets **0.1.0a1** for
**September 15, 2026** and **0.1.0** for **October 1, 2026**. See
STATUS.md, ROADMAP.md, and CHANGELOG.md for aligned progress. Phase 3
(stabilization/testing/documentation) and Phase 4 activities remain planned.

## Status

The dependency pins for `fastapi` (>=0.116.1) and `slowapi` (==0.1.9) remain
confirmed in `pyproject.toml` and [installation.md](installation.md), but the
evaluation environment still omits the Go Task CLI. `uv run task check` fails
with `No such file or directory` until `scripts/setup.sh` installs the binary.
Running `uv sync --extra dev-minimal --extra test` followed by
`uv run python scripts/check_env.py` leaves only the missing Go Task warning in
this setup. 【8e4fc3†L1-L27】【37a1fe†L1-L26】 Targeted unit runs on **September 17,
2025** show that the config validator, DuckDB offline fallback, and VSS
extension loader now pass with the `[test]` extras installed. 【5b737c†L1-L3】
【a7a5ea†L1-L2】【93e5f9†L1-L2】 Integration ranking checks and optional extras
still pass with the `[test]` extras installed. 【9a935a†L1-L2】【ee8c19†L1-L2】
However, `uv run pytest tests/unit -q` now fails in teardown because
monitor CLI metrics tests patch `ConfigLoader.load_config` to return
`type("C", (), {})()`. The autouse `cleanup_storage` fixture raises
`AttributeError: 'C' object has no attribute 'storage'`, so the suite stops
before distributed scenarios run. `uv run pytest tests/unit -k "storage" -q
--maxfail=1` reproduces the failure at
`tests/unit/test_monitor_cli.py::test_metrics_skips_storage`.
【eeec82†L1-L57】 `uv run mkdocs build` still fails until the
docs extras add `mkdocs` to the PATH, so run `task docs` (or `uv run
--extra docs mkdocs build`) to install them automatically. 【3109f7†L1-L3】
`task verify` remains blocked by the missing CLI and the storage teardown
regression, so coverage numbers are still unavailable. These items are tracked
in STATUS.md and the open issues listed there.
## Milestones

- **0.1.0a1** (2026-09-15, status: in progress): Alpha preview to collect
  feedback.
- **0.1.0** (2026-10-01, status: planned): Finalized packaging, docs and CI
  checks with all tests passing.
- **0.1.1** (2026-12-15, status: planned): Bug fixes and documentation
  updates (deliver-bug-fixes-and-docs-update).
- **0.2.0** (2027-03-01, status: planned): API stabilization, configuration
  hot-reload and improved search backends.
  - stabilize-api-and-improve-search
    - streaming-webhook-refinements
    - configuration-hot-reload-tests
    - hybrid-search-ranking-benchmarks
- **0.3.0** (2027-06-01, status: planned): Distributed execution support and
  monitoring utilities.
  - simulate-distributed-orchestrator-performance
- **1.0.0** (2027-09-01, status: planned): Full feature set, performance
  tuning and stable interfaces
  (reach-stable-performance-and-interfaces).

To gather early feedback, an alpha **0.1.0a1** release is targeted for
**September 15, 2026**. The final **0.1.0** milestone is set for
**October 1, 2026** while packaging tasks are resolved.

### Alpha release checklist

- [x] Confirm STATUS.md and this plan share the same coverage details before
  tagging. CI runs `scripts/update_coverage_docs.py` after `task coverage` to
  sync the value.
- [x] Ensure Task CLI available (restore-task-cli-availability).
- [x] Resolve coverage hang (fix-task-verify-coverage-hang).

These tasks completed in order: environment bootstrap → packaging verification
→ integration tests → coverage gates → algorithm validation.

### Prerequisites for tagging 0.1.0a1

- `uv run flake8 src tests` passed with no issues.
- `uv run mypy src` passed with no issues.
- `task verify` and `task coverage` executed with Go Task 3.44.1.
- Dry-run publish to TestPyPI succeeded using `uv run scripts/publish_dev.py`
  with `--dry-run --repository testpypi`.

The **0.1.0a1** date is re-targeted for **September 15, 2026** and the release
remains in progress until these prerequisites are satisfied.

Completion of these items confirms the alpha baseline for **0.1.0**.

## Release Phases

1. **Planning** – finalize scope and update the roadmap.
2. **Development** – implement features and expand test coverage.
3. **Stabilization** – fix bugs, write documentation and run the full test
   suite.
4. **Publish** – follow the workflow in `deployment.md`: run
   `task bump-version -- <new-version>`, run tests, publish to TestPyPI using
   `./scripts/publish_dev.py`, then release to PyPI with `twine upload dist/*`.

Each milestone may include additional patch releases for critical fixes.

## Packaging Workflow

1. `task bump-version -- <new-version>`
2. `uv pip install build twine`
3. `uv build`
4. `uv run twine check dist/*`
5. `uv run python scripts/publish_dev.py --dry-run`
6. Set `TWINE_USERNAME` and `TWINE_PASSWORD` then run
   `uv run twine upload --repository testpypi dist/*`
7. After verifying TestPyPI, publish to PyPI with
   `uv run twine upload dist/*`.

## CI Checklist

Before tagging **0.1.0**, ensure the following checks pass. `task verify`
syncs with `--python-platform x86_64-manylinux_2_28` to prefer wheels. It
installs only `dev-minimal` and `test` extras by default; add groups with
`EXTRAS`, e.g. `EXTRAS="nlp ui"` or `EXTRAS="gpu"`:

- [ ] `uv run flake8 src tests`
- [ ] `uv run mypy src`
- [ ] `uv run pytest -q`
- [ ] `uv run pytest tests/behavior`
- [ ] `task coverage` reports **90% coverage** for targeted modules; keep docs
  in sync and stay above **90%**
- [ ] `scripts/update_coverage_docs.py` syncs docs with
  `baseline/coverage.xml`

