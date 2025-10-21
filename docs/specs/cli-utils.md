# CLI Utils

## Overview

CLI utilities for consistent formatting and accessibility. The upcoming
terminal experience work layers Textual dashboards, prompt-toolkit prompts, and
Rich renderables on top of the existing Typer flows without breaking
automation-friendly fallbacks.

## Algorithms

- Implement core behaviors described above.

## Invariants

- CLI options resolve to deterministic defaults when unspecified.
- Output formatting preserves ANSI codes and width constraints.
- Help text lists commands in alphabetical order.
- Prompt abstraction selects prompt-toolkit only when a TTY and dependency
  check succeed; otherwise Typer handles the prompt.
- Rich renderables provide ASCII fallbacks whenever bare mode or non-TTY
  contexts are detected.
- Textual dashboards launch only when `sys.stdout.isatty()` and bare mode are
  satisfied, and they exit cleanly without corrupting stdout.

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
