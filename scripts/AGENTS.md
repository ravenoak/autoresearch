# Script Guidelines

These instructions apply to files in the `scripts/` directory.

## Usage
- Provide a clear CLI interface or usage comment at the top of each script.
- Validate inputs and fail fast on incorrect usage.
- Invoke Python scripts via `uv run` to ensure dependencies resolve.

## Safety
- Avoid destructive actions without an explicit confirmation flag.
- Do not require elevated privileges or modify user system settings.

## Cross-platform
- Use POSIX-compliant shell features or portable Python constructs.
- Test on Linux and macOS; avoid hard-coded paths and file extensions.
