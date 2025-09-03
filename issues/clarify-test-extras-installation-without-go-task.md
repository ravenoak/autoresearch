# Clarify test extras installation without Go Task

## Context
Running `uv run task check` fails when the Go Task CLI is absent, and direct
invocation of `uv run pytest` raises `ImportError: No module named 'pytest_bdd'`
when test extras are missing. The current status notes a manual workaround, but
readers may overlook the requirement to install `[test]` extras before executing
any pytest commands.

## Dependencies
None.

## Acceptance Criteria
- Update documentation to emphasize installing `[test]` extras when the Go Task
  CLI is unavailable.
- Provide a short example showing `uv pip install -e ".[test]"` before running
  pytest.
- Link the documentation from `STATUS.md` or setup instructions.

## Status
Open
