# Cli Utils

## Overview

CLI utilities for consistent formatting and accessibility.

## Algorithms

- Implement core behaviors described above.

## Invariants

- CLI options resolve to deterministic defaults when unspecified.
- Output formatting preserves ANSI codes and width constraints.
- Help text lists commands in alphabetical order.

## Proof Steps

1. Parse an empty argument list and record resolved defaults.
2. Override options to confirm user input supersedes defaults.
3. Inspect help output and verify alphabetical ordering.

## Simulation Expectations

Unit tests cover nominal and edge cases for these routines.

## Traceability


- Modules
  - [src/autoresearch/cli_utils.py][m1]
- Tests
  - [tests/unit/test_cli_utils_extra.py][t1]

[m1]: ../../src/autoresearch/cli_utils.py
[t1]: ../../tests/unit/test_cli_utils_extra.py
