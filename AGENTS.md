# Autoresearch Guidelines

## Project Snapshot
- **Purpose:** AI-assisted research orchestration framework.
- **Primary language:** Python.
- **Key outputs:** Library, CLI, and documentation for automated research
  workflows.

## Setup
- Run `task install` to initialize the Python 3.12+ environment and install
  hooks or dependencies.
- Use **uv** for package management; prefix standalone Python commands with
  `uv run`.
- For provisioning issues within this evaluation, `scripts/codex_setup.sh`
  bootstraps the Codex environment. It is Codex-specific, non-generic, and
  must not be referenced outside AGENTS.md files or the script itself. Use
  `scripts/setup.sh` for any other environment. It installs the project in
  editable mode and records the DuckDB vector extension path in `.env.offline`.

## Testing
- `task check` – run early for linting, type checks, and a fast test suite.
- `task verify` – run before committing; executes linting, type checks, and
  the full test suite with coverage.
- `task clean` – remove build artifacts.
- For testing details see `docs/testing_guidelines.md` (load only if needed).
- See `tests/AGENTS.md` for test markers and extras.

## Conventions
- Follow PEP 8 with 4-space indentation.
- Format with **black** and ensure **flake8** passes.
- Keep lines ≤ 100 characters and include docstrings for public APIs.
- Additional style guidance lives in `CONTRIBUTING.md` (load only if needed).

## Reasoning and Continuous Improvement
- Use dialectical and Socratic reasoning: state assumptions, question them,
  explore alternatives, and synthesize conclusions.
- Ground decisions in foundational values of clarity, safety, and
  maintainability.
- Record key reasoning in commits and pull requests.
- Reflect after completing tasks and update AGENTS files when workflows
  evolve.

## AGENTS.md Compliance
- Only `scripts/codex_setup.sh` may mention `AGENTS.md`; keep it aligned with
  these instructions. Do not reference `scripts/codex_setup.sh` outside this
  AGENTS.md system or the script itself.
- This file's scope is the entire repository; nested `AGENTS.md` files override
  these rules.
- This AGENTS.md follows the [AGENTS.md spec](https://gist.github.com) and acts
  as an initial memory; consult nested files for scoped guidance.
- For extensive details, consult docs under `docs/` as required.

## Changelog
- 2025-08-21: Clarified Codex-only scope for `scripts/codex_setup.sh` and
  restricted references to AGENTS files.
- 2025-08-20: Restructured instructions, added dialectical reasoning and
  continuous improvement guidance, and cited AGENTS.md spec.
- 2025-08-19: Added project snapshot, environment steps, Task commands,
  coding conventions, and AGENTS referencing policy.
- 2025-08-19: Added `AGENTS.md` for [src](src/AGENTS.md),
  [scripts](scripts/AGENTS.md), and [examples](examples/AGENTS.md).
- 2025-08-19: Documented `uv` usage and added guidelines for the
  `extensions/` directory.
- 2025-08-19: Trimmed redundant instructions and enforced 80-character lines
  across AGENTS files.

