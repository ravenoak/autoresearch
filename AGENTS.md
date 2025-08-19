# Autoresearch Guidelines

## Snapshot
- **Purpose:** AI-assisted research orchestration framework.
- **Primary language:** Python.
- **Key outputs:** Library, CLI, and documentation for automated research
  workflows.

## Environment
- Run `task install` to initialize the Python 3.12+ environment and install
  hooks or dependencies.
- Use **uv** for package management; prefix standalone Python commands
  with `uv run`.

## Build and Test
- `task check` – quick lint, type check, and test run.
- `task verify` – run before committing; performs linting, type checks, and
  the full test suite with coverage.
- `task clean` – remove build artifacts.
- For testing details see `docs/testing_guidelines.md` (load only if needed).
- See `tests/AGENTS.md` for test markers and extras.

## Coding Conventions
- Follow PEP 8 with 4-space indentation.
- Format with **black** and ensure **flake8** passes.
- Keep lines ≤ 100 characters and include docstrings for public APIs.
- Additional style guidance lives in `CONTRIBUTING.md` (load only if needed).

## Dialectical Process
- Apply a Socratic approach: state assumptions, question them, compare
  alternatives, and refine based on evidence.
- Document reasoning steps in commits and discussions.

## Policy
- Only `scripts/codex_setup.sh` may mention `AGENTS.md`; keep it aligned
  with these instructions.
- This file's scope is the entire repository; nested `AGENTS.md` files
  override these rules.
- For extensive details, consult docs under `docs/` as required.

## Changelog
- 2025-08-19: Added project snapshot, environment steps, Task commands,
  coding conventions, and AGENTS referencing policy.
- 2025-08-19: Added `AGENTS.md` for [src](src/AGENTS.md),
  [scripts](scripts/AGENTS.md), and [examples](examples/AGENTS.md).
- 2025-08-19: Documented `uv` usage and added guidelines for the
  `extensions/` directory.
- 2025-08-19: Trimmed redundant instructions and enforced 80-character
  lines across AGENTS files.

