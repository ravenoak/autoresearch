# Autoresearch Roadmap

This roadmap summarizes planned features for upcoming releases. Dates and milestones align with the [release plan](docs/release_plan.md).
Installation and environment details are covered in the [README](README.md).
Last updated **August 19, 2025**. For current test and coverage status, see
[docs/release_plan.md](docs/release_plan.md). Use Python 3.12+ with
`uv venv && uv sync --all-extras && uv pip install -e '.[full,parsers,git,llm,dev]'`
before running tests.
## Milestones

| Version | Target Date | Key Goals |
| ------- | ----------- | --------- |
| 0.1.0-alpha.1 | 2026-03-01 | Alpha preview to collect feedback while resolving test suite failures and aligning environment requirements ([resolve-test-failures], [align-environment-reqs]) |
| 0.1.0 | 2026-07-01 | Finalize packaging, docs and CI checks with all tests passing ([resolve-test-failures], [update-release-documentation]) |
| 0.1.1 | 2026-09-15 | Bug fixes and documentation updates |
| 0.2.0 | 2026-12-01 | API stabilization, configuration hot-reload, improved search backends |
| 0.3.0 | 2027-03-01 | Distributed execution support, monitoring utilities |
| 1.0.0 | 2027-06-01 | Full feature set, performance tuning and stable interfaces |

### Blockers before 0.1.0-alpha.1

| Blocker | Related Issue |
| ------- | ------------- |
| Test suite failures and missing dependencies | [resolve-test-failures] |
| Development environment misaligned with Python 3.12 and dev tooling | [align-environment-reqs] |
| Packaging scripts require configuration | [update-release-documentation] |

## 0.1.0-alpha.1 – Alpha preview

This pre-release provides an early package for testing while packaging tasks
remain open. Related issues
([resolve-test-failures],
[align-environment-reqs])
track outstanding test and environment work. Key activities include:

- Provide an installable package for early adopters.
- Collect feedback while fixing failing tests and packaging issues.
- Align development environment with project requirements (Python 3.12 and
  dev tooling).

## 0.1.0 – First public preview

The final 0.1.0 release focuses on making the project installable and
providing complete documentation once the open issues are resolved. Key
activities include:

- Running all unit, integration and behavior tests.
- Finalizing API reference and user guides.
- Verifying packaging metadata and TestPyPI uploads.

Type checking and tests still fail (see
[resolve-test-failures]), so
integration and behavior suites remain blocked. The release was originally
planned for **July 20, 2025**, but the schedule slipped. The **0.1.0**
milestone is now targeted for **July 1, 2026** while packaging tasks are
resolved.

## 0.1.1 – Bug fixes and documentation updates

Before publishing 0.1.0 the release plan lists several checks:
- Verify all automated tests pass in CI.
- Review documentation for clarity using a Socratic approach.
- Conduct a dialectical evaluation of core workflows.
- Ensure packaging metadata and publish scripts work correctly.

Any remaining issues from these tasks will be addressed in 0.1.1.
- CLI backup commands and testing utilities remain pending, while specialized agents—Moderator, Specialist, and User—are already implemented (`src/autoresearch/agents/specialized/moderator.py`, `src/autoresearch/agents/specialized/domain_specialist.py`, `src/autoresearch/agents/specialized/user_agent.py`) and will receive comprehensive unit tests once testing passes.
The 0.1.1 release is planned for **September 15, 2026**.

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


[resolve-test-failures]: issues/archive/resolve-current-test-failures.md
[align-environment-reqs]: issues/align-environment-with-requirements.md
[update-release-documentation]: issues/archive/update-release-documentation.md
