# Script Guidelines

These instructions apply to files in the `scripts/` directory.

## Snapshot
- **Purpose:** automation utilities and environment helpers.
- **Primary languages:** Bash and Python.
- **Key outputs:** CLI tools and setup scripts.
- `codex_setup.sh` bootstraps only the Codex evaluation environment and must
  not be referenced outside AGENTS.md files or the script itself. It installs
  the project in editable mode and updates `.env.offline` with the DuckDB
  vector extension path.

## Conventions
- Provide a clear CLI interface or usage comment at the top of each script.
- Validate inputs and fail fast on incorrect usage.
- Invoke Python scripts via `uv run` to ensure dependencies resolve.
- Avoid destructive actions without an explicit confirmation flag.
- Do not require elevated privileges or modify user system settings.
- Use POSIX-compliant shell features or portable Python constructs.
- Test on Linux and macOS; avoid hard-coded paths and file extensions.

## Reasoning and Continuous Improvement
- Explain nontrivial logic with inline comments referencing design choices.
- Record updates in commit messages when scripts evolve.

## AGENTS.md Compliance
- Scope: `scripts/` directory; nested `AGENTS.md` files override these rules.
- This AGENTS.md follows the [AGENTS.md spec](https://gist.github.com).
