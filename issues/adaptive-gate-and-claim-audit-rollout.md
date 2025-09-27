# Adaptive gate and claim audit rollout

## Context
The dialectical review highlighted that we need a scout pass and gate policy to
reduce cost on easy queries while keeping per-claim verification reliable. This
issue tracks Phase 1 of the deep research program, covering gating heuristics,
configuration toggles, and audit table plumbing so downstream clients can
inspect support status for every claim.

## Dependencies
- [prepare-first-alpha-release](prepare-first-alpha-release.md)

## Acceptance Criteria
- Gate policy module computes overlap, conflict, multi-hop, and graph
  contradiction signals, and exposes configuration thresholds with documented
  defaults.
- Scout pass drafts answers, persists supporting snippets, and records signals
  for telemetry and user overrides.
- Claim extraction and iterative retrieval produce per-claim audit records with
  status, entailment score, stability indicator, and citation metadata.
- Response payloads include audit tables and gate decisions for CLI, API, and
  UI clients, with documentation updates in `docs/output_formats.md`.
- Unit and integration tests cover gate decisions, override behavior, and audit
  serialization.

## Status
Open
