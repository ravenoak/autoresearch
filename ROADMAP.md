# Autoresearch Roadmap

This roadmap summarizes planned features for upcoming releases. Dates and milestones align with the [release plan](docs/release_plan.md).
Last updated **August 3, 2025**.
Phase 2 testing tasks are still in progress, so Phase 3 (stabilization/testing/documentation) items remain planned.

## Milestones

| Version | Target Date | Key Goals |
| ------- | ----------- | --------- |
| 0.1.0 | TBD | Finalize packaging, docs and CI checks |
| 0.1.1 | 2026-02-01 | Bug fixes and documentation updates |
| 0.2.0 | 2026-04-15 | API stabilization, configuration hot-reload, improved search backends |
| 0.3.0 | 2026-07-15 | Distributed execution support, monitoring utilities |
| 1.0.0 | 2026-10-01 | Full feature set, performance tuning and stable interfaces |

## 0.1.0 – First public preview

The initial release focuses on making the project installable and providing
complete documentation. Key activities include:

- Running all unit, integration and behavior tests.
- Finalizing API reference and user guides.
- Verifying packaging metadata and TestPyPI uploads.

Tests are still failing due to configuration errors and overall coverage is below the **90%** target.
Final package validation and documentation work remain in progress. The
**0.1.0** release date is now **TBD** until these Phase 2 tasks pass.

## 0.1.1 – Bug fixes and documentation updates

Before publishing 0.1.0 the release plan lists several checks:
- Verify all automated tests pass in CI.
- Review documentation for clarity using a Socratic approach.
- Conduct a dialectical evaluation of core workflows.
- Ensure packaging metadata and publish scripts work correctly.

Any remaining issues from these tasks will be addressed in 0.1.1.
- CLI backup commands, testing utilities and all specialized agents are
  planned to have full implementations and comprehensive unit tests once
  testing passes.
The 0.1.1 release is planned for **February 1, 2026**.

## 0.2.0 – API stabilization and improved search

The next minor release focuses on API improvements and search enhancements:
- Complete all search backends with cross-backend ranking and embedding-based search (see tasks in CODE_COMPLETE_PLAN lines 38-46).
- Add streaming responses and webhook notifications to the REST API (implemented per TASK_PROGRESS lines 143-150).
- Support hybrid keyword/semantic search and a unified ranking algorithm.
- Continue refining the web interface and visualization tools.

## 0.3.0 – Distributed execution and monitoring

Key features planned for this release include:
- Distributed agent execution across processes and storage backends (see CODE_COMPLETE_PLAN lines 156-160 and TASK_PROGRESS lines 182-192).
- Coordination mechanisms for distributed agents and parallel search.
- Expanded monitoring including real-time metrics and GPU usage.

## 1.0.0 – Stable interfaces and performance tuning

The 1.0.0 milestone aims for a polished, production-ready system:
- Complete packaging for all platforms with containerization support (CODE_COMPLETE_PLAN lines 168-176; TASK_PROGRESS lines 194-204).
- Provide deployment scripts and configuration validation (CODE_COMPLETE_PLAN lines 178-186; TASK_PROGRESS lines 206-216).
- Optimize performance across all components and finalize documentation.

