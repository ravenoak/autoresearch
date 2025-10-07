# Main Entrypoint

## Overview

`__main__` enables running Autoresearch with `python -m autoresearch`. It
imports the CLI application from `main.app` and executes it when invoked as a
script.

## Algorithms

- Import `app` from `autoresearch.main`.
- When `__name__ == "__main__"`, call `app()`.

## Invariants

- `app` is exposed in the module namespace.
- Executing the module triggers exactly one `app` call.

## Proof Sketch

`tests/unit/legacy/test_main_module.py` patches `app` and confirms it runs when the
module is executed as `__main__`.

## Simulation Expectations

- Running `uv run python -m autoresearch` invokes the CLI.
- Importing `autoresearch.__main__` without execution leaves `app` idle.

## Traceability

- Code: [src/autoresearch/__main__.py][m1]
- Tests: [tests/unit/legacy/test_main_module.py][t1]

[m1]: ../../src/autoresearch/__main__.py
[t1]: ../../tests/unit/legacy/test_main_module.py
