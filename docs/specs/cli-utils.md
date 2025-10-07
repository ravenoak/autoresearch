# CLI Utils

## Overview

CLI utilities for consistent formatting and accessibility.

## Algorithms

- Implement core behaviors described above.

## Invariants

- CLI options resolve to deterministic defaults when unspecified.
- Output formatting preserves ANSI codes and width constraints.
- Help text lists commands in alphabetical order.

## Proof Sketch

The parser resolves defaults for empty input, accepts user overrides, and
outputs alphabetical help text. The simulation in
[tests/unit/legacy/test_cli_utils_extra.py][t1] exercises these paths and
confirms all invariants.

## Simulation Expectations

Unit tests simulate argument parsing and help output for nominal and edge
cases.

## Traceability


- Modules
  - [src/autoresearch/cli_utils.py][m1]
- Tests
  - [tests/unit/legacy/test_cli_utils_extra.py][t1]

[m1]: ../../src/autoresearch/cli_utils.py
[t1]: ../../tests/unit/legacy/test_cli_utils_extra.py
