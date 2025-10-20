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

1. **Phase 1 – PySide6 POC Implementation (2 weeks)**
   - Announce limited support status for Streamlit in release notes.
   - Freeze new feature work on Streamlit modules.
2. **Phase 2 – Feature Parity Implementation (6 weeks)**
   - Maintain parity tracking dashboard comparing Streamlit and PySide6.
   - Schedule end-user testing sessions to validate PySide6 coverage.
3. **Phase 3 – Professional Features (4 weeks)**
   - Publish migration FAQ and collect final feedback from Streamlit power
     users.
   - Begin tagging Streamlit issues with `sunset` label for weekly review.
4. **Phase 4 – Testing and Quality Assurance (3 weeks)**
   - Deliver release candidate of PySide6 client and extend legacy support by
     six weeks for critical fixes only.
   - Confirm availability of the migration guide and hands-on onboarding
     sessions.
5. **Phase 5 – Deprecation and Removal (2 weeks)**
   - Mark Streamlit interface as deprecated in all documentation.
   - Announce final support date (two releases after Phase 5 completes) and
     outline archival schedule.

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
