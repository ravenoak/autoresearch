# Status

As of **August 4, 2025**, running `scripts/codex_setup.sh` installs Go Task but
leaves `.venv/bin` outside `PATH`. After exporting `PATH`, `task check` fails
because `uv sync --extra dev-minimal` removes `pytest_bdd`, `freezegun`, and
`hypothesis`. `scripts/check_env.py` reports these modules missing, so `task
check` and `task verify` exit early without running tests. Extension bootstrap was
not reached.

## Lint, type checks, and spec tests
Not run due to environment failures.

## Targeted tests
Not run. `task verify` exits during environment checks.

## Integration tests
Not run.

## Behavior tests
Not run.

## Coverage
Not generated because `task verify` fails before executing tests.
