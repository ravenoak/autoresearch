# Extension Guidelines

These instructions apply to files in the `extensions/` directory.

## Snapshot
- **Purpose:** packaged addons such as DuckDB extensions.
- **Primary languages:** Python and compiled artifacts.
- **Key outputs:** extension modules and binary assets.

## Setup
- Run `task install` to ensure required tooling is available.
- Run `task check` before committing changes.

## Conventions
- Follow repository coding conventions and organize imports with `isort`'s
  default profile.
- Use `uv run` when invoking Python modules or scripts directly.

## Reasoning and Continuous Improvement
- Document compatibility assumptions and revisit as dependencies evolve.

## AGENTS.md Compliance
- Scope: `extensions/` directory; nested `AGENTS.md` files override these rules.
- This AGENTS.md follows the [AGENTS.md spec](https://gist.github.com).
