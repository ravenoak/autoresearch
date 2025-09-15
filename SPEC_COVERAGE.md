| Module | Spec | Proof/Simulation | Status |
| --- | --- | --- | --- |
| `autoresearch` | [autoresearch.md](docs/specs/autoresearch.md) | [t1], [t2] | OK |
| `autoresearch/__main__.py` | [main-entrypoint.md](docs/specs/main-entrypoint.md) | [t3] | OK |
| `autoresearch/a2a_interface.py` | [a2a-interface.md](docs/specs/a2a-interface.md) | [p1], [s1], [t4], [t1], [t5], [t6] | OK |
| `autoresearch/agents` | [agents.md](docs/specs/agents.md) | [s2], [t7], [t8], [t9], [t10] | OK |
| `autoresearch/api` | [api.md](docs/specs/api.md) | [p2], [p3], [p4], [p5], [p6], [s3], [s4], [t11], [t12], [t13], [t14], [t15], [t16], [t17], [t18], [t19], [t20], [t21], [t22], [t23] | OK |
| `autoresearch/api/middleware.py` | [api_rate_limiting.md](docs/specs/api_rate_limiting.md) | [p5], [t24] | OK |
| `autoresearch/cache.py` | [cache.md](docs/specs/cache.md) | [t25] | OK |
| `autoresearch/cli_backup.py` | [cli-backup.md](docs/specs/cli-backup.md) | [t26] | OK |
| `autoresearch/cli_helpers.py` | [cli-helpers.md](docs/specs/cli-helpers.md) | [t27] | OK |
| `autoresearch/cli_utils.py` | [cli-utils.md](docs/specs/cli-utils.md) | [t28] | OK |
| `autoresearch/config` | [config.md](docs/specs/config.md) | [p7], [t29], [t30], [t31], [t32], [t33], [t34], [t35] | OK |
| `autoresearch/config_utils.py` | [config-utils.md](docs/specs/config-utils.md) | [p8], [t33], [t34], [t35], [t36], [t37], [t38], [t39], [t40], [t41], [t42], [t43] | OK |
| `autoresearch/data_analysis.py` | [data-analysis.md](docs/specs/data-analysis.md) | [t44], [t45], [t46] | OK |
| `autoresearch/distributed` | [distributed.md](docs/specs/distributed.md) | [p9], [p10], [s5], [s6], [s7], [s8], [t47], [t48], [t49], [t50], [t2], [t51] | OK |
| `autoresearch/error_recovery.py` | [error-recovery.md](docs/specs/error-recovery.md) | [p11], [t52] | OK |
| `autoresearch/error_utils.py` | [error-utils.md](docs/specs/error-utils.md) | [t53] | OK |
| `autoresearch/errors.py` | [errors.md](docs/specs/errors.md) | [t34], [t39], [t54] | OK |
| `autoresearch/examples` | [examples.md](docs/specs/examples.md) | [t55] | OK |
| `autoresearch/extensions.py` | [extensions.md](docs/specs/extensions.md) | [t56], [t57] | OK |
| `autoresearch/interfaces.py` | [interfaces.md](docs/specs/interfaces.md) | [t58] | OK |
| `autoresearch/kg_reasoning.py` | [kg-reasoning.md](docs/specs/kg-reasoning.md) | [t59] | OK |
| `autoresearch/llm` | [llm.md](docs/specs/llm.md) | [p12], [p13], [t9], [t60], [t61], [t62] | OK |
| `autoresearch/llm/adapters.py` | [llm.md](docs/specs/llm.md) | [p12], [p13], [t9], [t60], [t61], [t62] | OK |
| `autoresearch/llm/capabilities.py` | [llm.md](docs/specs/llm.md) | [p12], [p13], [t9], [t60], [t61], [t62] | OK |
| `autoresearch/llm/registry.py` | [llm.md](docs/specs/llm.md) | [p12], [p13], [t9], [t60], [t61], [t62] | OK |
| `autoresearch/llm/token_counting.py` | [llm.md](docs/specs/llm.md) | [p12], [p13], [t9], [t60], [t61], [t62] | OK |
| `autoresearch/logging_utils.py` | [logging-utils.md](docs/specs/logging-utils.md) | [t63], [t64] | OK |
| `autoresearch/main` | [main.md](docs/specs/main.md) | [t65], [t66], [t67] | OK |
| `autoresearch/mcp_interface.py` | [mcp-interface.md](docs/specs/mcp-interface.md) | [t68], [t69] | OK |
| `autoresearch/models.py` | [models.md](docs/specs/models.md) | [p14], [t70] | OK |
| `autoresearch/monitor` | [monitor.md](docs/specs/monitor.md) | [p15], [s9], [t71], [t72], [t73] | OK |
| `autoresearch/orchestration` | [orchestration.md](docs/specs/orchestration.md) | [p16], [s10], [t74], [t75], [t76], [t77], [t78] | OK |
| `autoresearch/orchestration/metrics.py` | [metrics.md](docs/specs/metrics.md) | [p13], [s11], [t79], [t80] | OK |
| `autoresearch/orchestrator_perf.py` | [orchestrator-perf.md](docs/specs/orchestrator-perf.md)<br>[orchestrator_scheduling.md](docs/specs/orchestrator_scheduling.md) | [s12], [t81], [t82], [t83] | OK |
| `autoresearch/output_format.py` | [output-format.md](docs/specs/output-format.md) | [t84], [t85] | OK |
| `autoresearch/resource_monitor.py` | [resource-monitor.md](docs/specs/resource-monitor.md) | [p17], [s13], [t86], [t73] | OK |
| `autoresearch/scheduler_benchmark.py` | [scheduler-benchmark.md](docs/specs/scheduler-benchmark.md) | [t83] | OK |
| `autoresearch/search` | [search.md](docs/specs/search.md) | [t87], [t88], [t89], [t90], [t91], [t32], [t92], [t93] | OK |
| `autoresearch/search/ranking_convergence.py` | [search_ranking.md](docs/specs/search_ranking.md) | [t87], [t89], [t94] | OK |
| `autoresearch/storage.py` | [storage.md](docs/specs/storage.md) | [p18], [s14], [s15], [s16], [s17], [t90], [t95], [t96], [t93], [t97], [t98], [t99], [t100], [t101] | OK |
| `autoresearch/storage_backends.py` | [storage-backends.md](docs/specs/storage-backends.md) | [s18], [t96], [t56], [t102] | OK |
| `autoresearch/storage_backup.py` | [storage-backup.md](docs/specs/storage-backup.md) | [t103] | OK |
| `autoresearch/storage_utils.py` | [storage-utils.md](docs/specs/storage-utils.md) | [t104] | OK |
| `autoresearch/streamlit_app.py` | [streamlit-app.md](docs/specs/streamlit-app.md) | [t42] | OK |
| `autoresearch/streamlit_ui.py` | [streamlit-ui.md](docs/specs/streamlit-ui.md) | [t105] | OK |
| `autoresearch/synthesis.py` | [synthesis.md](docs/specs/synthesis.md) | [t106] | OK |
| `autoresearch/test_tools.py` | [test-tools.md](docs/specs/test-tools.md) | [t107] | OK |
| `autoresearch/token_budget.py` | [token-budget.md](docs/specs/token-budget.md) | [s11], [t79] | OK |
| `autoresearch/tracing.py` | [tracing.md](docs/specs/tracing.md) | [t108] | OK |
| `autoresearch/visualization.py` | [visualization.md](docs/specs/visualization.md) | [p19], [t109], [t110] | OK |
| `git` | [git.md](docs/specs/git.md) | [t111], [t112] | OK |
| `git/search.py` | [git-search.md](docs/specs/git-search.md) | [t112] | OK |

[t1]: tests/integration/test_a2a_interface.py
[t2]: tests/unit/test_distributed.py
[t3]: tests/unit/test_main_module.py
[p1]: docs/algorithms/a2a_interface.md
[s1]: scripts/a2a_concurrency_sim.py
[t4]: tests/behavior/features/a2a_interface.feature
[t5]: tests/unit/test_a2a_concurrency_sim.py
[t6]: tests/unit/test_a2a_interface.py
[s2]: scripts/agents_sim.py
[t7]: tests/analysis/test_agents_sim.py
[t8]: tests/unit/test_advanced_agents.py
[t9]: tests/unit/test_agents_llm.py
[t10]: tests/unit/test_specialized_agents.py
[p2]: docs/algorithms/api-authentication.md
[p3]: docs/algorithms/api_auth_error_paths.md
[p4]: docs/algorithms/api_authentication.md
[p5]: docs/algorithms/api_rate_limiting.md
[p6]: docs/algorithms/api_streaming.md
[s3]: scripts/api_auth_credentials_sim.py
[s4]: scripts/api_stream_order_sim.py
[t11]: tests/analysis/test_api_stream_order_sim.py
[t12]: tests/analysis/test_api_streaming_sim.py
[t13]: tests/integration/test_api_auth.py
[t14]: tests/integration/test_api_auth_middleware.py
[t15]: tests/integration/test_api_docs.py
[t16]: tests/integration/test_api_streaming.py
[t17]: tests/integration/test_api_streaming_webhook.py
[t18]: tests/unit/test_api.py
[t19]: tests/unit/test_api_auth_deps.py
[t20]: tests/unit/test_api_auth_middleware.py
[t21]: tests/unit/test_api_error_handling.py
[t22]: tests/unit/test_api_imports.py
[t23]: tests/unit/test_webhooks_logging.py
[t24]: tests/unit/test_property_api_rate_limit_bounds.py
[t25]: tests/unit/test_cache.py
[t26]: tests/unit/test_cli_backup_extra.py
[t27]: tests/unit/test_cli_helpers.py
[t28]: tests/unit/test_cli_utils_extra.py
[p7]: docs/algorithms/config_hot_reload.md
[t29]: tests/analysis/config_hot_reload_metrics.json
[t30]: tests/analysis/test_config_hot_reload_sim.py
[t31]: tests/behavior/features/configuration_hot_reload.feature
[t32]: tests/integration/test_config_hot_reload_components.py
[t33]: tests/unit/test_config_env_file.py
[t34]: tests/unit/test_config_errors.py
[t35]: tests/unit/test_config_loader_defaults.py
[p8]: docs/algorithms/config_utils.md
[t36]: tests/unit/test_config_profiles.py
[t37]: tests/unit/test_config_reload.py
[t38]: tests/unit/test_config_utils.py
[t39]: tests/unit/test_config_validation_errors.py
[t40]: tests/unit/test_config_validators_additional.py
[t41]: tests/unit/test_config_watcher_cleanup.py
[t42]: tests/unit/test_streamlit_app_edgecases.py
[t43]: tests/unit/test_streamlit_utils.py
[t44]: tests/behavior/features/data_analysis.feature
[t45]: tests/unit/test_data_analysis.py
[t46]: tests/unit/test_kuzu_polars.py
[p9]: docs/algorithms/distributed_coordination.md
[p10]: docs/algorithms/distributed_overhead.md
[s5]: scripts/distributed_coordination_formulas.py
[s6]: scripts/distributed_coordination_sim.py
[s7]: scripts/distributed_recovery_benchmark.py
[s8]: scripts/orchestrator_distributed_sim.py
[t47]: tests/analysis/test_distributed_coordination.py
[t48]: tests/benchmark/test_orchestrator_distributed_sim.py
[t49]: tests/integration/test_distributed_agent_storage.py
[t50]: tests/unit/distributed/test_coordination_properties.py
[t51]: tests/unit/test_distributed_extra.py
[p11]: docs/algorithms/error_recovery.md
[t52]: tests/unit/test_error_recovery.py
[t53]: tests/unit/test_error_utils_additional.py
[t54]: tests/unit/test_errors.py
[t55]: tests/unit/test_examples_package.py
[t56]: tests/unit/test_duckdb_storage_backend.py
[t57]: tests/unit/test_vss_extension_loader.py
[t58]: tests/unit/test_interfaces.py
[t59]: tests/unit/test_kg_reasoning.py
[p12]: docs/algorithms/llm_adapter.md
[p13]: docs/algorithms/token_budgeting.md
[t60]: tests/unit/test_llm_adapter.py
[t61]: tests/unit/test_llm_capabilities.py
[t62]: tests/unit/test_token_usage.py
[t63]: tests/unit/test_logging_utils.py
[t64]: tests/unit/test_logging_utils_env.py
[t65]: tests/unit/test_main_backup_commands.py
[t66]: tests/unit/test_main_cli.py
[t67]: tests/unit/test_main_config_commands.py
[t68]: tests/behavior/features/mcp_interface.feature
[t69]: tests/unit/test_mcp_interface.py
[p14]: docs/algorithms/models.md
[t70]: tests/unit/test_models_docstrings.py
[p15]: docs/algorithms/monitor_cli.md
[s9]: scripts/monitor_cli_reliability.py
[t71]: tests/unit/test_main_monitor_commands.py
[t72]: tests/unit/test_monitor_cli.py
[t73]: tests/unit/test_resource_monitor_gpu.py
[p16]: docs/algorithms/orchestration.md
[s10]: scripts/orchestration_sim.py
[t74]: tests/unit/orchestration/test_budgeting_algorithm.py
[t75]: tests/unit/orchestration/test_circuit_breaker_determinism.py
[t76]: tests/unit/orchestration/test_circuit_breaker_thresholds.py
[t77]: tests/unit/orchestration/test_parallel_execute.py
[t78]: tests/unit/orchestration/test_parallel_merge_invariant.py
[s11]: scripts/token_budget_convergence.py
[t79]: tests/unit/test_metrics_token_budget_spec.py
[t80]: tests/unit/test_token_budget_convergence.py
[s12]: scripts/orchestrator_perf_sim.py
[t81]: tests/integration/test_orchestrator_performance.py
[t82]: tests/unit/test_orchestrator_perf_sim.py
[t83]: tests/unit/test_scheduler_benchmark.py
[t84]: tests/behavior/features/output_formatting.feature
[t85]: tests/unit/test_output_format.py
[p17]: docs/algorithms/resource_monitor.md
[s13]: scripts/resource_monitor_bounds.py
[t86]: tests/integration/test_monitor_metrics.py
[t87]: tests/behavior/features/hybrid_search.feature
[t88]: tests/behavior/features/local_sources.feature
[t89]: tests/behavior/features/search_cli.feature
[t90]: tests/behavior/features/storage_search_integration.feature
[t91]: tests/behavior/features/vector_search_performance.feature
[t92]: tests/integration/test_search_regression.py
[t93]: tests/integration/test_search_storage.py
[t94]: tests/benchmark/test_hybrid_ranking.py
[p18]: docs/algorithms/storage.md
[s14]: scripts/ram_budget_enforcement_sim.py
[s15]: scripts/schema_idempotency_sim.py
[s16]: scripts/storage_concurrency_sim.py
[s17]: scripts/storage_eviction_sim.py
[t95]: tests/integration/storage/test_simulation_benchmarks.py
[t96]: tests/integration/test_rdf_persistence.py
[t97]: tests/integration/test_storage_duckdb_fallback.py
[t98]: tests/integration/test_storage_eviction.py
[t99]: tests/targeted/test_storage_eviction.py
[t100]: tests/unit/test_storage_eviction.py
[t101]: tests/unit/test_storage_eviction_sim.py
[s18]: scripts/oxigraph_backend_sim.py
[t102]: tests/unit/test_duckdb_storage_backend_extended.py
[t103]: tests/unit/test_storage_backup.py
[t104]: tests/integration/test_storage_schema.py
[t105]: tests/unit/test_streamlit_ui_helpers.py
[t106]: tests/behavior/features/synthesis.feature
[t107]: tests/unit/test_test_tools.py
[t108]: tests/behavior/features/tracing.feature
[p19]: docs/algorithms/visualization.md
[t109]: tests/behavior/features/visualization_cli.feature
[t110]: tests/unit/test_visualization.py
[t111]: tests/integration/test_local_git_backend.py
[t112]: tests/targeted/test_git_search.py
