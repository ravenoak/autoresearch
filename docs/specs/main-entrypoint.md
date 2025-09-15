# Main Entrypoint

## Overview

Gateway for running the CLI with `python -m autoresearch`.

## Algorithms

- Imports `app` from `autoresearch.main`.
- Calls `app()` only when `__name__ == "__main__"`.

## Invariants

- Delegation ensures a single CLI entry path.

## Proof Sketch

[docs/algorithms/__main__.md](../algorithms/__main__.md) outlines the
logic. The unit test `tests/unit/test_main_module.py` patches the Typer app
to verify it runs exactly once.

## Simulation Expectations

- Executing the test demonstrates that `python -m autoresearch` invokes
the CLI application.

## Traceability

- Code: [src/autoresearch/__main__.py][m1]
- Tests: [tests/unit/test_main_module.py][t1]

[m1]: ../../src/autoresearch/__main__.py
[t1]: ../../tests/unit/test_main_module.py
