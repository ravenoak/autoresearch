# Streamlit Support Sunset Plan

## Overview

This document replaces the previous refactoring plan and summarizes the
remaining support expectations for the legacy Streamlit interface while the
project migrates to PySide6. It aligns timelines with the phases defined in the
PySide6 migration roadmap and documents the milestones for sunsetting,
communicating with users, and archiving Streamlit assets.

## Support Expectations

- **Critical fixes only**: After Phase 1 of the PySide6 migration (see the
  [PySide6 migration timeline][pyside6-timeline]), which covers the two-week
  proof-of-concept build, Streamlit receives security and stability patches
  only. Feature requests are
  routed to the PySide6 track.
- **Bug triage window**: During Phase 2 (six weeks) we continue triaging
  Streamlit regressions that block production workflows. Issues without
  workarounds are patched within two minor releases.
- **Compatibility assurance**: Until the close of Phase 3 (four additional
  weeks) we guarantee compatibility with supported Python and backend service
  versions. Deprecated APIs receive warnings but remain available.
- **Legacy user support window**: Beginning with Phase 4 (three weeks) we offer
  a six-week grace period for legacy Streamlit users. During this window we
  publish weekly status updates, host office hours, and prioritize migration
  assistance over new fixes.
- **Migration guidance**: See the
  [Streamlit to PySide6 migration guide](../guides/streamlit-to-pyside6.md) for
  feature parity tracking, the desktop extra setup checklist, troubleshooting
  steps, and FAQs targeted at legacy teams.

## Sunset Milestones

The following milestones mirror the PySide6 migration phases to ensure a
coordinated transition:

1. **Phase 1 – PySide6 POC Implementation (2 weeks)** (targets
   [0.1.0a1][release-0-1-0a1])
   - Announce limited support status for Streamlit in release notes.
   - Freeze new feature work on Streamlit modules.
   - **Checklist**
     - [ ] Communication: Publish Streamlit support downgrade in release notes
       and the champion newsletter.
     - [ ] CLI gating: Capture `AUTORESEARCH_ENABLE_STREAMLIT` launch logs in
       the Phase 1 QA report.
     - [ ] Archive prep: Inventory Streamlit-only assets earmarked for Phase 5
       migration.
2. **Phase 2 – Feature Parity Implementation (6 weeks)** (targets the
   [0.1.0 beta checkpoint][release-0-1-0-beta])
   - Maintain parity tracking dashboard comparing Streamlit and PySide6.
   - Schedule end-user testing sessions to validate PySide6 coverage.
   - **Checklist**
     - [ ] Communication: Circulate the parity dashboard update and migration
       FAQ preview.
     - [ ] CLI gating: Verify opt-in gating across supported shells and record
       evidence in the CLI validation spreadsheet.
     - [ ] Archive prep: Stage Streamlit analytics bundles for read-only
       archival in `archive/streamlit/`.
3. **Phase 3 – Professional Features (4 weeks)** (targets the
   [0.1.0 release candidate build][release-0-1-0-rc])
   - Publish migration FAQ and collect final feedback from Streamlit power
     users.
   - Begin tagging Streamlit issues with `sunset` label for weekly review.
   - **Checklist**
     - [ ] Communication: Deliver customer webinar recap and distribute the
       PySide6 migration worksheet.
     - [ ] CLI gating: Confirm release candidate builds log deprecation
       warnings when the flag is unset.
     - [ ] Archive prep: Export Streamlit issue labels and attach them to the
       archive manifest.
4. **Phase 4 – Testing and Quality Assurance (3 weeks)** (targets the
   [0.1.0 general availability milestone][release-0-1-0-ga])
   - Deliver release candidate of PySide6 client and extend legacy support by
     six weeks for critical fixes only.
   - Confirm availability of the migration guide and hands-on onboarding
     sessions.
   - **Checklist**
     - [ ] Communication: Include PySide6 readiness notes and Streamlit sunset
       reminders in release candidate communications.
     - [ ] CLI gating: Run regression verifying exit messaging when the flag is
       absent and store the transcript in the QA matrix.
     - [ ] Archive prep: Transfer Streamlit documentation PDFs into the
       release archive staging bucket.
5. **Phase 5 – Deprecation and Removal (2 weeks)** (targets the
   [0.1.1 maintenance release][release-0-1-1])
   - Mark Streamlit interface as deprecated in all documentation.
   - Announce final support date (two releases after Phase 5 completes) and
     outline archival schedule.
   - **Checklist**
     - [ ] Communication: Publish sunset closure note referencing the final
       migration guide update.
     - [ ] CLI gating: Confirm the default CLI path blocks launch and links to
       the archive notice.
     - [ ] Archive prep: Finalize asset moves and sign off on the archive
       manifest with Change Champions.

## Archival Steps

1. **Final verification**
   - Run the Streamlit regression suite one final time at the close of the
     extended grace period.
   - Capture the last known good configuration in `docs/releases/legacy/`.
2. **Repository reorganization**
   - Move Streamlit-specific modules, tests, and fixtures to
     `archive/streamlit/` with read-only status.
   - Update import guards so Streamlit code executes only when explicitly
     enabled via environment variable (e.g., `AUTORESEARCH_ENABLE_STREAMLIT`).
3. **Documentation update**
   - Replace Streamlit usage instructions with migration pointers and PySide6
     onboarding steps across the documentation set.
   - Link the archived plan and regression results from
     `docs/releases/legacy/index.md`.
4. **Post-archive monitoring**
   - Maintain an LTS branch for three months to accept critical security fixes
     requested by enterprise deployments.
   - Review telemetry and support tickets monthly to confirm PySide6 adoption
     and retire the LTS branch once demand subsides.

This plan ensures Streamlit users receive clear communication, defined support
windows, and actionable migration paths while the PySide6 experience becomes
the default interface.

[pyside6-timeline]: ../pyside6_migration_plan.md#migration-timeline
[release-0-1-0a1]: ../../release_notes.md#010a1-planned
[release-0-1-0-beta]: ../../release_plan.md#milestones
[release-0-1-0-rc]: ../../release_plan.md#milestones
[release-0-1-0-ga]: ../../release_plan.md#milestones
[release-0-1-1]: ../../release_plan.md#milestones
