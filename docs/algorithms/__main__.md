# Command-Line Entrypoint

Runs the CLI when the package is executed with `python -m autoresearch`.

## Invariants

- Delegates to `main.app` for a single point of CLI invocation.
- Executes the application only when `__name__ == "__main__"`.

## References

- [`__main__.py`](../../src/autoresearch/__main__.py)
- [../specs/main.md](../specs/main.md)
