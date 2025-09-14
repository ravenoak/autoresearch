# Limit verify extras for local runs

## Context
Running `task verify` with default settings pulls every optional extra,
triggering over 80 package downloads. Local contributors need a way to run a
lighter verify for quick iterations.

## Dependencies
- [resolve-resource-tracker-errors-in-verify](resolve-resource-tracker-errors-in-verify.md)

## Acceptance Criteria
- Verify task accepts an option or documented workflow to run with minimal extras.
- README and testing guidelines mention how to run verify with reduced downloads.
- STATUS.md notes the reduced download approach.

## Status
Open
