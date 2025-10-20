# Streamlit Sunset Runbook

## Purpose

This runbook equips Change Champions with the operational steps required to
retire the Streamlit interface while guiding teams toward the PySide6 desktop
experience. Follow the timeline checkpoints, coordinate with the listed owners,
and be ready to roll back if critical adoption risks emerge.

## Roles and Owners

- **Executive Sponsor:** Priya Shah – approves exit criteria and rollback
  activation.
- **Program Lead:** Mateo Ortiz – coordinates cross-team updates and runbook
  reviews.
- **QA Lead:** Lila Singh – maintains CLI gating evidence and validation logs.
- **Documentation Steward:** Alana Chen – synchronizes migration guides and
  release notes.
- **DevOps Liaison:** Ruben Flores – executes archival moves and monitors
  deployment health.

## Timeline Overview

| Phase | Window | Change Champion Focus |
| --- | --- | --- |
| Phase 1 / 0.1.0a1 | 2 weeks | Deliver support downgrade messaging. |
| | | Log baseline CLI gating verification. |
| | | Complete asset inventory. |
| Phase 2 / 0.1.0 beta | 6 weeks | Share parity dashboard updates. |
| | | Harden CLI gating coverage. |
| | | Stage analytics bundles for archive. |
| Phase 3 / 0.1.0 RC | 4 weeks | Publish migration FAQ refresh. |
| | | Collect feedback logs. |
| | | Export Streamlit issue metadata. |
| Phase 4 / 0.1.0 GA | 3 weeks | Confirm warning copy alignment. |
| | | Package documentation updates. |
| | | Prepare archive transfers. |
| Phase 5 / 0.1.1 | 2 weeks | Issue final sunset notice. |
| | | Enforce default CLI block. |
| | | Complete archive manifest sign-off. |

## Phase Checklists

### Phase 1 – PySide6 POC Implementation (targets 0.1.0a1)

1. Confirm release notes include the Streamlit support downgrade and migration
   link.
2. Capture `AUTORESEARCH_ENABLE_STREAMLIT` launch logs in the QA repository.
3. Produce asset inventory spreadsheet for modules, tests, and docs slated for
   archival.

### Phase 2 – Feature Parity Implementation (targets 0.1.0 beta)

1. Distribute parity dashboard snapshot during the Change Champion stand-up.
2. Validate CLI gating on Linux, macOS, and Windows shells; attach evidence to
   the QA matrix.
3. Stage analytics bundles and telemetry exports inside `archive/streamlit/`.

### Phase 3 – Professional Features (targets 0.1.0 RC)

1. Publish updated migration FAQ and circulate webinar recap notes.
2. Ensure CLI builds emit deprecation warnings when the flag is absent.
3. Export Streamlit GitHub label history and add it to the archive manifest.

### Phase 4 – Testing and Quality Assurance (targets 0.1.0 GA)

1. Verify release candidate warning copy matches migration guide wording.
2. Archive CLI transcripts and screenshots in `qa/streamlit/phase4.md`.
3. Move documentation PDFs and legacy diagrams into the release archive bucket.

### Phase 5 – Deprecation and Removal (targets 0.1.1)

1. Announce the final Streamlit support date and reference the migration guide
   addendum.
2. Confirm the CLI blocks legacy launch by default and links to the archive
   notice.
3. Obtain sign-off from Executive Sponsor and Program Lead on the archive
   manifest.

## Rollback Guidance

- **Trigger conditions:** Unexpected adoption blockers, compliance escalations,
  or regression in the PySide6 client affecting critical workflows.
- **Immediate actions:** Pause archival scripts, revert environment variable
  gating commit, and announce the rollback in the Change Champion channel.
- **Recovery window:** Maintain a hotfix branch for 14 days with the prior
  Streamlit assets while remediation proceeds.
- **Re-entry criteria:** All high-severity issues resolved, updated migration
  instructions published, and Change Champions approve reinstating the timeline.

## Communication Artifacts

- Weekly Change Champion digest summarizing sunset status, blockers, and next
  actions.
- Release notes callouts referencing the latest migration guide updates.
- FAQ and webinar recap stored alongside QA evidence for audit readiness.

## References

- [Streamlit refactor plan](../specs/streamlit-refactor-plan.md)
- [Streamlit maintenance spec](../specs/streamlit-ui.md)
- [Streamlit to PySide6 migration guide](../guides/streamlit-to-pyside6.md)
