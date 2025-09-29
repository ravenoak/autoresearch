# Adaptive gate and claim audit rollout

## Context
The dialectical review highlighted that we need a scout pass and gate policy to
reduce cost on easy queries while keeping per-claim verification reliable. This
issue tracks Phase 1 of the deep research program, covering gating heuristics,
configuration toggles, and audit table plumbing so downstream clients can
inspect support status for every claim.

## Dependencies
- [prepare-first-alpha-release](../prepare-first-alpha-release.md)

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

## Resolution
- `task verify` at 17:45 UTC and `task coverage` at 18:19 UTC now capture the
  VSS loader replay, scout gate telemetry, and audit tables that satisfy the
  gating acceptance criteria.【F:baseline/logs/task-verify-20250930T174512Z.log†L1-L23】
  【F:baseline/logs/task-coverage-20250930T181947Z.log†L1-L21】
- `docs/deep_research_upgrade_plan.md` and `docs/release_plan.md` describe the
  CLI toggles, layered exports, and release-trail linkage produced during
  testing.【F:docs/deep_research_upgrade_plan.md†L18-L45】【F:docs/release_plan.md†L18-L33】
- `issues/prepare-first-alpha-release.md` threads the verify, coverage, and
  packaging logs so reviewers can audit the gating evidence without rerunning
  the sweep.【F:issues/prepare-first-alpha-release.md†L4-L27】

## Status
Archived
