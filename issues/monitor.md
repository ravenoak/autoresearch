# Document monitor telemetry helpers

## Context
Monitor utilities now expose helpers for normalising claim audit payloads and
aggregating status counters for dashboards. The documentation previously
described only the Prometheus surface, leaving the telemetry API implicit.

## Dependencies
- None

## Acceptance Criteria
- Describe the telemetry helpers in `docs/monitoring.md`.
- Ensure monitor telemetry functions emit the canonical audit fields.
- Cover the helpers and environment metadata providers with unit tests.

## Status
Archived
