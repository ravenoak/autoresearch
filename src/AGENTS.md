# Source Code Guidelines

These instructions apply to files in the `src/` directory.

## Coding style
- Follow repository conventions.
- Organize imports with `isort`'s default profile.

## Docstrings
- Provide Google-style docstrings for all public classes, functions, and
  modules.
- Include `Args`, `Returns`, and `Raises` sections when applicable.

## Type checking
- Use explicit type hints for function signatures and critical variables.
- Run `task check` to validate types before committing. When invoking tools
  directly, prefix them with `uv run`.
