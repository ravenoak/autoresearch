# Source Code Guidelines

These instructions apply to files in the `src/` directory.

## Snapshot
- **Purpose:** core library implementation.
- **Primary language:** Python.
- **Key outputs:** reusable modules and packages.

## Setup
- Run `task install` to ensure dependencies and hooks are present.
- Run `task check` for quick validation and `task verify` before committing.

## Conventions
- Follow repository coding conventions and organize imports with `isort`'s
  default profile.
- Provide Google-style docstrings for all public classes, functions, and
  modules, including `Args`, `Returns`, and `Raises` when applicable.
- Use explicit type hints for function signatures and critical variables.
- When invoking tools directly, prefix them with `uv run`.
- When applying the current date, derive it from the system time.

## Reasoning and Continuous Improvement
- Challenge algorithmic choices and document trade-offs in comments.
- Record significant design decisions in commit messages or docs.

## AGENTS.md Compliance
- Scope: `src/` directory; nested `AGENTS.md` files override these rules.
- This AGENTS.md follows the [AGENTS.md spec](https://gist.github.com).
