# Autoresearch Roadmap

This roadmap summarizes planned features for upcoming releases. Dates and milestones align with the [release plan](docs/release_plan.md).
Last updated **August 18, 2025**.
Phase 2 testing tasks remain incomplete: `uv run flake8 src tests` passes,
`uv run mypy src` fails with `Error importing plugin "pydantic.mypy": No
module named 'pydantic'`, and `uv run pytest -q` reports 30 collection
errors including missing `pytest_bdd`, so integration and behavior suites
remain failing. To collect feedback while checks stabilize,
[resolve-current-test-failures](issues/resolve-current-test-failures.md)
remains open, and an alpha pre-release precedes the final 0.1.0
milestone.
## Milestones

| Version | Target Date | Key Goals |
| ------- | ----------- | --------- |
| 0.1.0-alpha.1 | 2026-02-15 | Alpha preview to collect feedback while resolving test suite failures ([resolve-current-test-failures](issues/resolve-current-test-failures.md)) |
| 0.1.0 | 2026-06-01 | Finalize packaging, docs and CI checks with all tests passing ([resolve-current-test-failures](issues/resolve-current-test-failures.md), [update-release-documentation](issues/archive/update-release-documentation.md)) |
| 0.1.1 | 2026-08-15 | Bug fixes and documentation updates |
| 0.2.0 | 2026-11-01 | API stabilization, configuration hot-reload, improved search backends |
| 0.3.0 | 2027-01-15 | Distributed execution support, monitoring utilities |
| 1.0.0 | 2027-04-01 | Full feature set, performance tuning and stable interfaces |

## 0.1.0-alpha.1 – Alpha preview

This pre-release provides an early package for testing while packaging tasks
remain open. Related issue
([resolve-current-test-failures](issues/resolve-current-test-failures.md))
is open. Key activities include:

- Provide an installable package for early adopters.
- Collect feedback while fixing failing tests and packaging issues.

## 0.1.0 – First public preview

The final 0.1.0 release focuses on making the project installable and
providing complete documentation once the open issues are resolved. Key
activities include:

- Running all unit, integration and behavior tests.
- Finalizing API reference and user guides.
- Verifying packaging metadata and TestPyPI uploads.

Type checking and tests still fail (see
[resolve-current-test-failures](issues/resolve-current-test-failures.md)), so
integration and behavior suites remain blocked. The release was originally
planned for **July 20, 2025**, but the schedule slipped. The **0.1.0**
milestone is now targeted for **June 1, 2026** while packaging tasks are
resolved.

## 0.1.1 – Bug fixes and documentation updates

Before publishing 0.1.0 the release plan lists several checks:
- Verify all automated tests pass in CI.
- Review documentation for clarity using a Socratic approach.
- Conduct a dialectical evaluation of core workflows.
- Ensure packaging metadata and publish scripts work correctly.

Any remaining issues from these tasks will be addressed in 0.1.1.
- CLI backup commands and testing utilities remain pending, while specialized agents—Moderator, Specialist, and User—are already implemented (`src/autoresearch/agents/specialized/moderator.py`, `src/autoresearch/agents/specialized/domain_specialist.py`, `src/autoresearch/agents/specialized/user_agent.py`) and will receive comprehensive unit tests once testing passes.
The 0.1.1 release is planned for **August 15, 2026**.

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

