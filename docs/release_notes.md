# Release Notes

Autoresearch is a local-first research assistant that coordinates multiple
agents to produce evidence-backed answers and stores data on the user's
machine.

## 0.1.0a1 (Planned)

Planned for release after comprehensive testing and documentation verification.
Dependency pins: `fastapi>=0.116.1` and `slowapi==0.1.9`.

### Core Features

- **Multi-Agent Research Orchestration**: Coordinates dialectical, contrarian, and fact-checking agents to synthesize evidence-backed answers.
- **Local-First Architecture**: Uses local databases (DuckDB, Kuzu) for searches and knowledge graphs, ensuring user data privacy.
- **Flexible Query Modes**: Supports direct, dialectical, and chain-of-thought reasoning modes for different research scenarios.
- **Pluggable Backends**: Modular search and storage backends enable local-first workflows with optional cloud integrations.
- **Comprehensive APIs**: Provides both command-line interface and HTTP REST API for programmatic access.

### Advanced Capabilities

- **Agent Communication Framework**: Sophisticated message passing and state management between specialized agents.
- **Knowledge Graph Integration**: Automatic entity extraction, relationship inference, and graph-based reasoning.
- **Adaptive Search Strategies**: Multi-backend search with ranking, caching, and fallback mechanisms.
- **Circuit Breaker Protection**: Robust error handling and recovery mechanisms for distributed agent coordination.
- **Real-time Monitoring**: Comprehensive metrics, logging, and observability for research workflows.

### Optional Enhancements

- **Desktop Interface**: PySide6-based native desktop application for professional research workflows.
- **Distributed Processing**: Ray and Redis support for scalable agent coordination.
- **Vector Search**: DuckDB VSS extension integration for semantic search capabilities.
- **Document Processing**: PDF, DOCX, and web content parsing for comprehensive research inputs.

### Known Limitations

- Fresh environments omit the Go Task CLI, so `task --version` reports
  `command not found` until Task is installed (for example via
  `scripts/setup.sh`).
- `uv run mkdocs build` fails with `No such file or directory` until the docs
  extras install `mkdocs`; run `task docs` or `uv run --extra docs`
  `mkdocs build` beforehand.
- `uv run pytest tests/unit -q` aborts when monitor metrics tests patch
  `ConfigLoader.load_config` to objects without `storage`; the autouse
  `cleanup_storage` fixture raises `AttributeError` during teardown.

For installation and usage instructions see the README.

### Open issues

- handle-config-loader-patches-in-storage-teardown
- prepare-first-alpha-release
- resolve-resource-tracker-errors-in-verify
- restore-distributed-coordination-simulation-exports

## Packaging Logs

### Build

```text
* Creating isolated environment: venv+pip...
* Installing packages in isolated environment:
  - poetry-core>=2.0.0,<3.0.0
* Getting build dependencies for sdist...
* Building sdist...
* Building wheel from sdist
* Creating isolated environment: venv+pip...
* Installing packages in isolated environment:
  - poetry-core>=2.0.0,<3.0.0
* Getting build dependencies for wheel...
* Building wheel...
Successfully built autoresearch-0.1.0a1.tar.gz and autoresearch-0.1.0a1-py3-none-any.whl
```

### Test Publishing

Dry-run upload using ``scripts/publish_dev.py --dry-run --repository testpypi``
on 2025-08-29 produced:

```text
* Creating isolated environment: venv+pip...
* Installing packages in isolated environment:
  - poetry-core>=2.0.0,<3.0.0
* Getting build dependencies for sdist...
* Building sdist...
* Building wheel from sdist
* Creating isolated environment: venv+pip...
* Installing packages in isolated environment:
  - poetry-core>=2.0.0,<3.0.0
* Getting build dependencies for wheel...
* Building wheel...
Successfully built autoresearch-0.1.0a1.tar.gz and autoresearch-0.1.0a1-py3-none-any.whl
Dry run selected; skipping upload
```
The build completed and, as expected for a dry run, the upload was skipped.
