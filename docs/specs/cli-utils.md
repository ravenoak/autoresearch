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
`tests/unit/test_cli_utils_extra.py` exercises these paths and confirms all
invariants.

## Simulation Expectations

Unit tests simulate argument parsing and help output for nominal and edge
cases.
