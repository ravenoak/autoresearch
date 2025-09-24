| Module | Spec | Proof/Simulation | Status |
| --- | --- | --- | --- |
| `autoresearch` | [autoresearch.md](docs/specs/autoresearch.md) | [t1], [t2] | OK |
| `autoresearch/__main__.py` | [main-entrypoint.md](docs/specs/main-entrypoint.md) | [t3] | OK |
| `autoresearch/a2a_interface.py` | [a2a-interface.md](docs/specs/a2a-interface.md) | [p1], [s1], [t4], [t1], [t5], [t6] | OK |
| `autoresearch/agents` | [agents.md](docs/specs/agents.md) | [s2], [t7], [t8], [t9], [t10] | OK |
| `autoresearch/agents/dialectical/contrarian.py` | [agents-dialectical.md](docs/specs/agents-dialectical.md) | [p2], [s3], [t11], [t12], [t9], [t13], [t14] | OK |
| `autoresearch/agents/dialectical/fact_checker.py` | [agents-dialectical.md](docs/specs/agents-dialectical.md) | [p2], [s3], [t11], [t12], [t9], [t13], [t14] | OK |
| `autoresearch/agents/dialectical/synthesizer.py` | [agents-dialectical.md](docs/specs/agents-dialectical.md) | [p2], [s3], [t11], [t12], [t9], [t13], [t14] | OK |
| `autoresearch/agents/specialized/critic.py` | [agents-specialized.md](docs/specs/agents-specialized.md) | [t8], [t10] | OK |
| `autoresearch/agents/specialized/domain_specialist.py` | [agents-specialized.md](docs/specs/agents-specialized.md) | [t8], [t10] | OK |
| `autoresearch/agents/specialized/moderator.py` | [agents-specialized.md](docs/specs/agents-specialized.md) | [t8], [t10] | OK |
| `autoresearch/agents/specialized/planner.py` | [agents-specialized.md](docs/specs/agents-specialized.md) | [t8], [t10] | OK |
| `autoresearch/agents/specialized/researcher.py` | [agents-specialized.md](docs/specs/agents-specialized.md) | [t8], [t10] | OK |
| `autoresearch/agents/specialized/summarizer.py` | [agents-specialized.md](docs/specs/agents-specialized.md) | [t8], [t10] | OK |
| `autoresearch/agents/specialized/user_agent.py` | [agents-specialized.md](docs/specs/agents-specialized.md) | [t8], [t10] | OK |
| `autoresearch/api` | [api.md](docs/specs/api.md) | [p3], [p4], [p5], [p6], [p7], [s4], [s5], [t15], [t16], [t17], [t18], [t19], [t20], [t21], [t22], [t23], [t24], [t25], [t26], [t27], [t28], [t29], [t30], [t31], [t32] | OK |
| `autoresearch/api/auth_middleware.py` | [api.md](docs/specs/api.md) | [p3], [p4], [p5], [p6], [p7], [s4], [s5], [t15], [t16], [t17], [t18], [t19], [t20], [t21], [t22], [t23], [t24], [t25], [t26], [t27], [t28], [t29], [t30], [t31], [t32] | OK |
| `autoresearch/api/middleware.py` | [api.md](docs/specs/api.md)<br>[api_rate_limiting.md](docs/specs/api_rate_limiting.md) | [p3], [p4], [p5], [p6], [p7], [s4], [s5], [t15], [t16], [t17], [t18], [t19], [t20], [t21], [t22], [t23], [t24], [t25], [t26], [t27], [t28], [t29], [t30], [t31], [t33], [t32] | OK |
| `autoresearch/api/routing.py` | [api.md](docs/specs/api.md) | [p3], [p4], [p5], [p6], [p7], [s4], [s5], [t15], [t16], [t17], [t18], [t19], [t20], [t21], [t22], [t23], [t24], [t25], [t26], [t27], [t28], [t29], [t30], [t31], [t32] | OK |
| `autoresearch/api/streaming.py` | [api.md](docs/specs/api.md) | [p3], [p4], [p5], [p6], [p7], [s4], [s5], [t15], [t16], [t17], [t18], [t19], [t20], [t21], [t22], [t23], [t24], [t25], [t26], [t27], [t28], [t29], [t30], [t31], [t32] | OK |
| `autoresearch/api/utils.py` | [api.md](docs/specs/api.md) | [p3], [p4], [p5], [p6], [p7], [s4], [s5], [t15], [t16], [t17], [t18], [t19], [t20], [t21], [t22], [t23], [t24], [t25], [t26], [t27], [t28], [t29], [t30], [t31], [t32] | OK |
| `autoresearch/cache.py` | [cache.md](docs/specs/cache.md) | [t34], [t135] | OK |
| `autoresearch/cli_backup.py` | [cli-backup.md](docs/specs/cli-backup.md) | [t35] | OK |
| `autoresearch/cli_helpers.py` | [cli-helpers.md](docs/specs/cli-helpers.md) | [t36] | OK |
| `autoresearch/cli_utils.py` | [cli-utils.md](docs/specs/cli-utils.md) | [t37] | OK |
| `autoresearch/config` | [config.md](docs/specs/config.md) | [p8], [p9], [t38], [t39], [t40], [t41], [t42], [t43], [t44], [t45], [t46], [t47], [t48] | OK |
| `autoresearch/config/loader.py` | [config.md](docs/specs/config.md) | [p8], [p9], [t38], [t39], [t40], [t41], [t42], [t43], [t44], [t45], [t46], [t47], [t48] | OK |
| `autoresearch/config/models.py` | [config.md](docs/specs/config.md) | [p8], [p9], [t38], [t39], [t40], [t41], [t42], [t43], [t44], [t45], [t46], [t47], [t48] | OK |
| `autoresearch/config/validators.py` | [config.md](docs/specs/config.md) | [p8], [p9], [t38], [t39], [t40], [t41], [t42], [t43], [t44], [t45], [t46], [t47], [t48] | OK |
| `autoresearch/config_utils.py` | [config-utils.md](docs/specs/config-utils.md) | [p10], [t42], [t43], [t44], [t45], [t46], [t49], [t47], [t50], [t48], [t51], [t52] | OK |
| `autoresearch/data_analysis.py` | [data-analysis.md](docs/specs/data-analysis.md) | [t53], [t54], [t55] | OK |
| `autoresearch/distributed` | [distributed.md](docs/specs/distributed.md) | [p11], [p12], [p13], [s6], [s7], [s8], [s9], [t56], [t57], [t58], [t59], [t2], [t60] | OK |
| `autoresearch/distributed/broker.py` | [distributed.md](docs/specs/distributed.md) | [p11], [p12], [p13], [s6], [s7], [s8], [s9], [t56], [t57], [t58], [t59], [t2], [t60] | OK |
| `autoresearch/distributed/coordinator.py` | [distributed.md](docs/specs/distributed.md) | [p11], [p12], [p13], [s6], [s7], [s8], [s9], [t56], [t57], [t58], [t59], [t2], [t60] | OK |
| `autoresearch/distributed/executors.py` | [distributed.md](docs/specs/distributed.md) | [p11], [p12], [p13], [s6], [s7], [s8], [s9], [t56], [t57], [t58], [t59], [t2], [t60], [t137] | OK |
| `autoresearch/error_recovery.py` | [error-recovery.md](docs/specs/error-recovery.md) | [p14], [t61] | OK |
| `autoresearch/error_utils.py` | [error-utils.md](docs/specs/error-utils.md) | [t62] | OK |
| `autoresearch/errors.py` | [errors.md](docs/specs/errors.md) | [t43], [t47], [t63] | OK |
| `autoresearch/examples` | [examples.md](docs/specs/examples.md) | [t64] | OK |
| `autoresearch/extensions.py` | [extensions.md](docs/specs/extensions.md) | [s10], [s11], [t65], [t66], [t67] | OK |
| `autoresearch/interfaces.py` | [interfaces.md](docs/specs/interfaces.md) | [t68] | OK |
| `autoresearch/kg_reasoning.py` | [kg-reasoning.md](docs/specs/kg-reasoning.md) | [t69] | OK |
| `autoresearch/llm` | [llm.md](docs/specs/llm.md) | [p15], [p16], [t9], [t70], [t71], [t72] | OK |
| `autoresearch/llm/adapters.py` | [llm.md](docs/specs/llm.md) | [p15], [p16], [t9], [t70], [t71], [t72] | OK |
| `autoresearch/llm/capabilities.py` | [llm.md](docs/specs/llm.md) | [p15], [p16], [t9], [t70], [t71], [t72] | OK |
| `autoresearch/llm/registry.py` | [llm.md](docs/specs/llm.md) | [p15], [p16], [t9], [t70], [t71], [t72] | OK |
| `autoresearch/llm/token_counting.py` | [llm.md](docs/specs/llm.md) | [p15], [p16], [t9], [t70], [t71], [t72] | OK |
| `autoresearch/logging_utils.py` | [logging-utils.md](docs/specs/logging-utils.md) | [t73], [t74] | OK |
| `autoresearch/main` | [main.md](docs/specs/main.md) | [t75], [t76], [t77] | OK |
| `autoresearch/mcp_interface.py` | [mcp-interface.md](docs/specs/mcp-interface.md) | [t78], [t79] | OK |
| `autoresearch/models.py` | [models.md](docs/specs/models.md) | [p17], [t80] | OK |
| `autoresearch/monitor` | [monitor.md](docs/specs/monitor.md) | [s12], [t81], [t82], [t83], [t84], [t85], [t86] | OK |
| `autoresearch/monitor/cli.py` | [monitor.md](docs/specs/monitor.md) | [s12], [t81], [t82], [t83], [t84], [t85], [t86] | OK |
| `autoresearch/monitor/metrics.py` | [monitor.md](docs/specs/monitor.md) | [s12], [t81], [t82], [t83], [t84], [t85], [t86] | OK |
| `autoresearch/monitor/node_health.py` | [monitor.md](docs/specs/monitor.md) | [s12], [t81], [t82], [t83], [t84], [t85], [t86] | OK |
| `autoresearch/monitor/system_monitor.py` | [monitor.md](docs/specs/monitor.md) | [s12], [t81], [t82], [t83], [t84], [t85], [t86] | OK |
| `autoresearch/orchestration` | [orchestration.md](docs/specs/orchestration.md) | [p18], [s13], [t87], [t88], [t89], [t90], [t91] | OK |
| `autoresearch/orchestration/metrics.py` | [metrics.md](docs/specs/metrics.md) | [p16], [s14], [t92], [t93], [t126], [t139] | OK (piecewise monotonic after first usage) |
| `autoresearch/orchestrator_perf.py` | [orchestrator-perf.md](docs/specs/orchestrator-perf.md)<br>[orchestrator_scheduling.md](docs/specs/orchestrator_scheduling.md) | [s15], [t94], [t95], [t96] | OK |
| `autoresearch/output_format.py` | [output-format.md](docs/specs/output-format.md) | [t97], [t98] | OK |
| `autoresearch/resource_monitor.py` | [monitor.md](docs/specs/monitor.md)<br>[resource-monitor.md](docs/specs/resource-monitor.md) | [p19], [s12], [s16], [t81], [t82], [t83], [t84], [t85], [t99], [t86] | OK |
| `autoresearch/scheduler_benchmark.py` | [scheduler-benchmark.md](docs/specs/scheduler-benchmark.md) | [t96] | OK |
| `autoresearch/search` | [search.md](docs/specs/search.md) | [t100], [t101], [t102], [t103], [t104], [t41], [t105], [t106], [t127], [t128], [t133], [t134], [t135], [t136], [t138] | OK (stable tie-break documented) |
| `autoresearch/search/parsers.py` | [search.md](docs/specs/search.md) | [t129], [t130], [t131], [t132] | OK |
| `autoresearch/search/ranking_convergence.py` | [search_ranking.md](docs/specs/search_ranking.md) | [t100], [t102], [t107] | OK (deterministic ranking proven) |
| `autoresearch/storage.py` | [storage.md](docs/specs/storage.md) | [p20], [s17], [s18], [s19], [s20], [s22], [t103], [t108], [t109], [t106], [t110], [t111], [t112], [t113], [t114], [t125] | OK (stale LRU fallback covered) |
| `autoresearch/storage_backends.py` | [storage-backends.md](docs/specs/storage-backends.md) | [s21], [t109], [t65], [t66] | OK |
| `autoresearch/storage_backup.py` | [storage-backup.md](docs/specs/storage-backup.md) | [t115] | OK |
| `autoresearch/storage_utils.py` | [storage-utils.md](docs/specs/storage-utils.md) | [t116] | OK |
| `autoresearch/streamlit_app.py` | [streamlit-app.md](docs/specs/streamlit-app.md) | [t51] | OK |
| `autoresearch/streamlit_ui.py` | [streamlit-ui.md](docs/specs/streamlit-ui.md) | [t117] | OK |
| `autoresearch/synthesis.py` | [synthesis.md](docs/specs/synthesis.md) | [t118] | OK |
| `autoresearch/test_tools.py` | [test-tools.md](docs/specs/test-tools.md) | [t119] | OK |
| `autoresearch/token_budget.py` | [token-budget.md](docs/specs/token-budget.md) | [s14], [t92], [t139] | OK |
| `autoresearch/tracing.py` | [tracing.md](docs/specs/tracing.md) | [t120] | OK |
| `autoresearch/visualization.py` | [visualization.md](docs/specs/visualization.md) | [p21], [t121], [t122] | OK |
| `git` | [git.md](docs/specs/git.md) | [t123], [t124] | OK |
| `git/search.py` | [git-search.md](docs/specs/git-search.md) | [t124] | OK |

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
[p2]: docs/algorithms/dialectical_coordination.md
[s3]: scripts/dialectical_coordination_demo.py
[t11]: tests/analysis/dialectical_cycle_analysis.py
[t12]: tests/analysis/test_dialectical_cycle_property.py
[t13]: tests/unit/test_property_dialectical_coordination.py
[t14]: tests/unit/test_synthesizer_agent_modes.py
[p3]: docs/algorithms/api-authentication.md
[p4]: docs/algorithms/api_auth_error_paths.md
[p5]: docs/algorithms/api_authentication.md
[p6]: docs/algorithms/api_rate_limiting.md
[p7]: docs/algorithms/api_streaming.md
[s4]: scripts/api_auth_credentials_sim.py
[s5]: scripts/api_stream_order_sim.py
[t15]: tests/analysis/test_api_stream_order_sim.py
[t16]: tests/analysis/test_api_streaming_sim.py
[t17]: tests/integration/test_api.py
[t18]: tests/integration/test_api_additional.py
[t19]: tests/integration/test_api_auth.py
[t20]: tests/integration/test_api_auth_middleware.py
[t21]: tests/integration/test_api_auth_permissions.py
[t22]: tests/integration/test_api_docs.py
[t23]: tests/integration/test_api_hot_reload.py
[t24]: tests/integration/test_api_streaming.py
[t25]: tests/integration/test_api_streaming_webhook.py
[t26]: tests/integration/test_api_versioning.py
[t27]: tests/unit/test_api.py
[t28]: tests/unit/test_api_auth_deps.py
[t29]: tests/unit/test_api_auth_middleware.py
[t30]: tests/unit/test_api_error_handling.py
[t31]: tests/unit/test_api_imports.py
[t32]: tests/unit/test_webhooks_logging.py
[t33]: tests/unit/test_property_api_rate_limit_bounds.py
[t34]: tests/unit/test_cache.py
[t35]: tests/unit/test_cli_backup_extra.py
[t36]: tests/unit/test_cli_helpers.py
[t37]: tests/unit/test_cli_utils_extra.py
[p8]: docs/algorithms/config_hot_reload.md
[p9]: docs/algorithms/config_weight_sum_simulation.md
[t38]: tests/analysis/config_hot_reload_metrics.json
[t39]: tests/analysis/test_config_hot_reload_sim.py
[t40]: tests/behavior/features/configuration_hot_reload.feature
[t41]: tests/integration/test_config_hot_reload_components.py
[t42]: tests/unit/test_config_env_file.py
[t43]: tests/unit/test_config_errors.py
[t44]: tests/unit/test_config_loader_defaults.py
[t45]: tests/unit/test_config_profiles.py
[t46]: tests/unit/test_config_reload.py
[t47]: tests/unit/test_config_validation_errors.py
[t48]: tests/unit/test_config_watcher_cleanup.py
[p10]: docs/algorithms/config_utils.md
[t49]: tests/unit/test_config_utils.py
[t50]: tests/unit/test_config_validators_additional.py
[t51]: tests/unit/test_streamlit_app_edgecases.py
[t52]: tests/unit/test_streamlit_utils.py
[t53]: tests/behavior/features/data_analysis.feature
[t54]: tests/unit/test_data_analysis.py
[t55]: tests/unit/test_kuzu_polars.py
[p11]: docs/algorithms/distributed_coordination.md
[p12]: docs/algorithms/distributed_overhead.md
[p13]: docs/algorithms/distributed_perf.md
[s6]: scripts/distributed_coordination_formulas.py
[s7]: scripts/distributed_coordination_sim.py
[s8]: scripts/distributed_recovery_benchmark.py
[s9]: scripts/orchestrator_distributed_sim.py
[t56]: tests/analysis/test_distributed_coordination.py
[t57]: tests/benchmark/test_orchestrator_distributed_sim.py
[t58]: tests/integration/test_distributed_agent_storage.py
[t59]: tests/unit/distributed/test_coordination_properties.py
[t60]: tests/unit/test_distributed_extra.py
[p14]: docs/algorithms/error_recovery.md
[t61]: tests/unit/test_error_recovery.py
[t62]: tests/unit/test_error_utils_additional.py
[t63]: tests/unit/test_errors.py
[t64]: tests/unit/test_examples_package.py
[s10]: scripts/download_duckdb_extensions.py
[s11]: scripts/smoke_test.py
[t65]: tests/unit/test_duckdb_storage_backend.py
[t66]: tests/unit/test_duckdb_storage_backend_extended.py
[t67]: tests/unit/test_vss_extension_loader.py
[t68]: tests/unit/test_interfaces.py
[t69]: tests/unit/test_kg_reasoning.py
[p15]: docs/algorithms/llm_adapter.md
[p16]: docs/algorithms/token_budgeting.md
[t70]: tests/unit/test_llm_adapter.py
[t71]: tests/unit/test_llm_capabilities.py
[t72]: tests/unit/test_token_usage.py
[t73]: tests/unit/test_logging_utils.py
[t74]: tests/unit/test_logging_utils_env.py
[t75]: tests/unit/test_main_backup_commands.py
[t76]: tests/unit/test_main_cli.py
[t77]: tests/unit/test_main_config_commands.py
[t78]: tests/behavior/features/mcp_interface.feature
[t79]: tests/unit/test_mcp_interface.py
[p17]: docs/algorithms/models.md
[t80]: tests/unit/test_models_docstrings.py
[s12]: scripts/monitor_cli_reliability.py
[t81]: tests/integration/test_monitor_metrics.py
[t82]: tests/unit/test_main_monitor_commands.py
[t83]: tests/unit/test_monitor_cli.py
[t84]: tests/unit/test_monitor_metrics_init.py
[t85]: tests/unit/test_node_health_monitor_property.py
[t86]: tests/unit/test_system_monitor.py
[p18]: docs/algorithms/orchestration.md
[s13]: scripts/orchestration_sim.py
[t87]: tests/unit/orchestration/test_budgeting_algorithm.py
[t88]: tests/unit/orchestration/test_circuit_breaker_determinism.py
[t89]: tests/unit/orchestration/test_circuit_breaker_thresholds.py
[t90]: tests/unit/orchestration/test_parallel_execute.py
[t91]: tests/unit/orchestration/test_parallel_merge_invariant.py
[s14]: scripts/token_budget_convergence.py
[t92]: tests/unit/test_metrics_token_budget_spec.py
[t93]: tests/unit/test_token_budget_convergence.py
[t126]: tests/unit/test_heuristic_properties.py
[s15]: scripts/orchestrator_perf_sim.py
[t94]: tests/integration/test_orchestrator_performance.py
[t95]: tests/unit/test_orchestrator_perf_sim.py
[t96]: tests/unit/test_scheduler_benchmark.py
[t97]: tests/behavior/features/output_formatting.feature
[t98]: tests/unit/test_output_format.py
[p19]: docs/algorithms/resource_monitor.md
[s16]: scripts/resource_monitor_bounds.py
[t99]: tests/unit/test_resource_monitor_gpu.py
[t100]: tests/behavior/features/hybrid_search.feature
[t101]: tests/behavior/features/local_sources.feature
[t102]: tests/behavior/features/search_cli.feature
[t103]: tests/behavior/features/storage_search_integration.feature
[t104]: tests/behavior/features/vector_search_performance.feature
[t105]: tests/integration/test_search_regression.py
[t106]: tests/integration/test_search_storage.py
[t107]: tests/benchmark/test_hybrid_ranking.py
[p20]: docs/algorithms/storage.md
[s17]: scripts/ram_budget_enforcement_sim.py
[s18]: scripts/schema_idempotency_sim.py
[s19]: scripts/storage_concurrency_sim.py
[s20]: scripts/storage_eviction_sim.py
[s22]: docs/algorithms/storage.md#setup-concurrency-metrics
[t108]: tests/integration/storage/test_simulation_benchmarks.py
[t109]: tests/integration/test_rdf_persistence.py
[t110]: tests/integration/test_storage_duckdb_fallback.py
[t111]: tests/integration/test_storage_eviction.py
[t112]: tests/targeted/test_storage_eviction.py
[t113]: tests/unit/test_storage_eviction.py
[t114]: tests/unit/test_storage_eviction_sim.py
[s21]: scripts/oxigraph_backend_sim.py
[t115]: tests/unit/test_storage_backup.py
[t116]: tests/integration/test_storage_schema.py
[t117]: tests/unit/test_streamlit_ui_helpers.py
[t118]: tests/behavior/features/synthesis.feature
[t119]: tests/unit/test_test_tools.py
[t120]: tests/behavior/features/tracing.feature
[p21]: docs/algorithms/visualization.md
[t121]: tests/behavior/features/visualization_cli.feature
[t122]: tests/unit/test_visualization.py
[t123]: tests/integration/test_local_git_backend.py
[t124]: tests/targeted/test_git_search.py
[t125]: tests/unit/test_storage_manager_concurrency.py
[t127]: tests/unit/test_search.py::test_external_lookup_vector_search
[t128]: tests/unit/test_search.py::test_external_lookup_hybrid_query
[t129]: tests/unit/test_search_parsers.py::test_extract_pdf_text
[t130]: tests/unit/test_search_parsers.py::test_extract_docx_text
[t131]: tests/unit/test_search_parsers.py::test_pdf_parser_errors_on_corrupt_file
[t132]: tests/unit/test_search_parsers.py::test_docx_parser_errors_on_corrupt_file
[t133]: tests/unit/test_search_parsers.py::test_search_local_file_backend
[t134]: tests/unit/test_relevance_ranking.py::test_calculate_semantic_similarity
[t135]: tests/unit/test_relevance_ranking.py::test_external_lookup_uses_cache
[t136]: tests/unit/test_property_bm25_normalization.py::test_bm25_scores_normalized
[t137]: tests/unit/test_distributed_executors.py::test_execute_agent_remote
[t138]: tests/unit/test_ranking_idempotence.py::test_rank_results_idempotent
[t139]: tests/unit/test_metrics_token_budget_spec.py::test_convergence_bound_holds
