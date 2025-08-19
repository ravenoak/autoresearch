# Extension Guidelines

These instructions apply to files in the `extensions/` directory.

## Coding style
- Follow repository conventions: PEP 8 with 4-space indentation and lines ≤100 characters.
- Organize imports with `isort`'s default profile.

## Tooling
- Run `task check` before committing changes.
- Use `uv run` when invoking Python modules or scripts directly.
