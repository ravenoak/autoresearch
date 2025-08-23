# Status

These results reflect the latest development state after attempting to run
tasks in a fresh environment. Refer to the
[roadmap](ROADMAP.md) and [release plan](docs/release_plan.md) for scheduled
milestones.

## `task check`
```text
FAILED tests/unit/test_failure_paths.py::test_vector_search_vss_unavailable - autoresearch.errors.StorageError: VSS extension...
FAILED tests/unit/test_main_cli.py::test_serve_command - assert 130 == 0
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! KeyboardInterrupt !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
```
Result: tests failed and run interrupted.

## `task verify`
```text
not run
```
Result: skipped due to earlier failures.

## `task coverage`
```text
not run
```
Result: coverage report not produced.
