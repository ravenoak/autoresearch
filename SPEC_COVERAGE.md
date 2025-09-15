| Module | Spec | Proof/Simulation | Status |
| --- | --- | --- | --- |
| `autoresearch` | [autoresearch.md](docs/specs/autoresearch.md) | [a1], [t1] | OK |
| `autoresearch/__main__.py` | [main-entrypoint.md](docs/specs/main-entrypoint.md) | [a2], [t2] | OK |
| `autoresearch/a2a_interface.py` | [a2a-interface.md](docs/specs/a2a-interface.md) |  | OK |
| `autoresearch/agents` | [agents.md](docs/specs/agents.md) | [agents.md](docs/algorithms/agents.md) | OK |
| `autoresearch/api` | [api.md](docs/specs/api.md) | [p1], [p2], [s1] | OK |
| `autoresearch/cache.py` | [cache.md](docs/specs/cache.md) | [cache.md](docs/algorithms/cache.md) | OK |
| `autoresearch/cli_backup.py` | [cli-backup.md](docs/specs/cli-backup.md) |  | OK |
| `autoresearch/cli_helpers.py` | [cli-helpers.md](docs/specs/cli-helpers.md) |  | Outdated spec |
| `autoresearch/cli_utils.py` | [cli-utils.md](docs/specs/cli-utils.md) |  | OK |
| `autoresearch/config` | [config.md](docs/specs/config.md) | [config.md](docs/algorithms/config.md) | Outdated spec |
| `autoresearch/config_utils.py` | [config-utils.md](docs/specs/config-utils.md) |  | OK |
| `autoresearch/data_analysis.py` | [data-analysis.md](docs/specs/data-analysis.md) |  | OK |
| `autoresearch/distributed` | [distributed.md](docs/specs/distributed.md) | [distributed.md](docs/algorithms/distributed.md) | Outdated spec |
| `autoresearch/error_recovery.py` | [error-recovery.md](docs/specs/error-recovery.md) |  | OK |
| `autoresearch/error_utils.py` | [error-utils.md](docs/specs/error-utils.md) |  | OK |
| `autoresearch/errors.py` | [errors.md](docs/specs/errors.md) | [errors.md](docs/algorithms/errors.md) | OK |
| `autoresearch/examples` | [examples.md](docs/specs/examples.md) | [examples.md](docs/algorithms/examples.md) | OK |
| `autoresearch/extensions.py` | [extensions.md](docs/specs/extensions.md) | [extensions.md](docs/algorithms/extensions.md) | Outdated spec |
| `autoresearch/interfaces.py` | [interfaces.md](docs/specs/interfaces.md) | [interfaces.md](docs/algorithms/interfaces.md) | OK |
| `autoresearch/kg_reasoning.py` | [kg-reasoning.md](docs/specs/kg-reasoning.md) |  | OK |
| `autoresearch/llm` | [llm.md](docs/specs/llm.md) | [llm.md](docs/algorithms/llm.md) | OK |
| `autoresearch/logging_utils.py` | [logging-utils.md](docs/specs/logging-utils.md) |  | OK |
| `autoresearch/main` | [main.md](docs/specs/main.md) | [main.md](docs/algorithms/main.md) | OK |
| `autoresearch/mcp_interface.py` | [mcp-interface.md](docs/specs/mcp-interface.md) |  | OK |
| `autoresearch/models.py` | [models.md](docs/specs/models.md) | [models.md](docs/algorithms/models.md) | OK |
| `autoresearch/monitor` | [monitor.md](docs/specs/monitor.md) | [monitor.md](docs/algorithms/monitor.md) | Outdated spec |
| `autoresearch/orchestration` | [orchestration.md](docs/specs/orchestration.md) | [orchestration.md](docs/algorithms/orchestration.md) | OK |
| `autoresearch/orchestrator_perf.py` | [orchestrator-perf.md](docs/specs/orchestrator-perf.md) | [a3], [s2] | OK |
| `autoresearch/output_format.py` | [output-format.md](docs/specs/output-format.md) |  | OK |
| `autoresearch/resource_monitor.py` | [resource-monitor.md](docs/specs/resource-monitor.md) |  | OK |
| `autoresearch/scheduler_benchmark.py` | [scheduler-benchmark.md](docs/specs/scheduler-benchmark.md) | [a4], [t3] | OK |
| `autoresearch/search` | [search.md](docs/specs/search.md) | [search.md](docs/algorithms/search.md) | OK |
| `autoresearch/storage.py` | [storage.md](docs/specs/storage.md) | [storage.md](docs/algorithms/storage.md) | OK |
| `autoresearch/storage_backends.py` | [storage-backends.md](docs/specs/storage-backends.md) |  | OK |
| `autoresearch/storage_backup.py` | [storage-backup.md](docs/specs/storage-backup.md) |  | OK |
| `autoresearch/storage_utils.py` | [storage-utils.md](docs/specs/storage-utils.md) |  | OK |
| `autoresearch/streamlit_app.py` | [streamlit-app.md](docs/specs/streamlit-app.md) |  | OK |
| `autoresearch/streamlit_ui.py` | [streamlit-ui.md](docs/specs/streamlit-ui.md) |  | OK |
| `autoresearch/synthesis.py` | [synthesis.md](docs/specs/synthesis.md) | [synthesis.md](docs/algorithms/synthesis.md) | OK |
| `autoresearch/test_tools.py` | [test-tools.md](docs/specs/test-tools.md) |  | OK |
| `autoresearch/token_budget.py` | [token-budget.md](docs/specs/token-budget.md) |  | OK |
| `autoresearch/tracing.py` | [tracing.md](docs/specs/tracing.md) | [tracing.md](docs/algorithms/tracing.md) | OK |
| `autoresearch/visualization.py` | [visualization.md](docs/specs/visualization.md) | [visualization.md](docs/algorithms/visualization.md) | OK |
| `git` | [git.md](docs/specs/git.md) | [t4], [t5] | OK |
| `git/search.py` | [git-search.md](docs/specs/git-search.md) |  | OK |
[p1]: docs/algorithms/api.md
[p2]: docs/algorithms/api-authentication.md
[s1]: scripts/api_auth_credentials_sim.py
[a1]: docs/algorithms/__init__.md
[t1]: tests/unit/test_version.py
[a2]: docs/algorithms/__main__.md
[t2]: tests/unit/test_main_module.py
[a3]: docs/algorithms/orchestrator_perf.md
[s2]: scripts/orchestrator_perf_sim.py
[a4]: docs/algorithms/scheduler_benchmark.md
[t3]: tests/unit/test_scheduler_benchmark.py
[t4]: tests/unit/test_git_repo_stub.py
[t5]: tests/targeted/test_git_search.py
