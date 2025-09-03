# Algorithms

- [BM25 Ranking Formula](bm25.md)
- [API Rate Limiting](api_rate_limiting.md)
- [API Authentication](api_authentication.md)
- [API Auth Error Paths](api_auth_error_paths.md)
- [Ontology Reasoning](ontology_reasoning.md)
- [Semantic Similarity](semantic_similarity.md)
- [Source Credibility](source_credibility.md)
- [Validation](validation.md)
- [Distributed Coordination](distributed_coordination.md)
- [Orchestration Simulations](orchestration.md)
- [Weight Tuning](weight_tuning.md)
- [Config Hot Reload](config_hot_reload.md)
- [Config Utils](config_utils.md)
- [Dialectical Agent Coordination](dialectical_coordination.md)
- [Token Budget Adaptation](token_budgeting.md)
- [Relevance Ranking](relevance_ranking.md)
- [Ranking Formula](ranking_formula.md)
- [Error Recovery via Exponential Backoff](error_recovery.md)
- [Cache Eviction Strategy](cache_eviction.md)
- [Storage Eviction](storage_eviction.md)
- [Resource Monitoring](resource_monitor.md)
- [Monitor CLI](monitor_cli.md)
- [Models](models.md)
- [Graph Visualization Pipeline](visualization.md)
- [Search Cache](cache.md)
- [CLI Helpers](cli_helpers.md)
- [Interfaces](interfaces.md)

## Proof and Simulation Coverage

### Completed
- Cache – simulation verifies linear eviction cost and correctness.
- Distributed coordination – leader election proof and performance simulation.
- Search – monotonic ranking proof and convergence simulation.
- ranking_formula – simulation compares ranking across noisy datasets.
- a2a_interface – simulation verifies agent messaging.
- api_rate_limiting – simulation tests request throttling.
- api_streaming – simulation exercises API streaming.
- bm25 – simulation checks ranking scores.
- cli_backup – simulation validates backup commands.
- cli_helpers – simulation tests CLI helper functions.
- cli_utils – simulation covers CLI utilities.
- config_hot_reload – simulation confirms live config reload.
- config_utils – simulation verifies config helpers.
- distributed_workflows – simulation models workflow distribution.
- error_utils – simulation checks error helpers.
- errors – simulation explores error scenarios.
- extensions – simulation exercises extension loading.
- interfaces – simulation verifies interface contracts.
- mcp_interface – simulation tests MCP interactions.
- models – simulation ensures model orchestration.
- ontology_reasoning – simulation validates reasoning.
- output_format – simulation checks formatting.
- resource_monitor – simulation monitors resources.
- search_ranking – simulation confirms ranking convergence.
- semantic_similarity – simulation verifies similarity scoring.
- streamlit_app – simulation covers UI flows.
- synthesis – simulation tests synthesis pipeline.
- test_tools – simulation exercises testing tools.
- tracing – simulation traces execution.
- visualization – simulation renders graphs.

### Pending
- None

## Contribution Notes

- Add a "Related Issues" section to each algorithm document linking to
  relevant planning tickets under `../../issues/`.
