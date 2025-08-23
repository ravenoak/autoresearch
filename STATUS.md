# Status

These results reflect the latest development state after attempting to run
tasks in a fresh environment. Refer to the
[roadmap](ROADMAP.md) and [release plan](docs/release_plan.md) for scheduled
milestones.

## `task check`
```text
task check
```
Result: 1 failed, 607 passed, 26 skipped, 24 deselected. Failing test:
`tests/unit/test_token_budget_convergence.py::test_suggest_token_budget_converges`.

## `task verify`
```text
task verify
```
Result: 2 failed, 606 passed, 26 skipped, 24 deselected. Failing tests:
`tests/unit/test_relevance_ranking.py::test_external_lookup_uses_cache`
and `tests/unit/test_token_budget_convergence.py::test_suggest_token_budget_converges`.

## `task coverage`
```text
task coverage
```
Result: command terminated before completion; coverage metrics unavailable.
