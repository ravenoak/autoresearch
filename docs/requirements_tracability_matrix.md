# Requirements Traceability Matrix

| Req ID | Description | Modules | Test(s) |
|--------|-------------|---------|---------|
| F-01 | CLI entry point | `main.py`, `api.py` | `tests/integration/test_cli_http.py`, `tests/behavior/features/query_interface.feature` |
| F-02 | Config via env/config file | `config.py` | `tests/unit/test_config_reload.py` |
| F-03 | Multiple LLM backends | `llm/` | `tests/unit/test_llm_adapter.py` |
| F-04 | Hybrid DKG persistence | `storage.py` | `tests/behavior/features/dkg_persistence.feature` |
| F-05 | Parallel search queries | `search.py` | `tests/integration/test_search_backends.py` |
| F-06 | Synthesize answers with LLM | `agents/dialectical/` | `tests/unit/test_agents_llm.py` |
| F-07 | Structured logging & metrics | `logging_utils.py`, `orchestration/metrics.py` | `tests/unit/test_metrics.py`, `tests/integration/test_monitor_metrics.py` |
| F-08 | Interactive mode | `main.py` | `tests/behavior/features/query_interface.feature` |
| F-09 | RAM budget and eviction | `storage.py` | `tests/unit/test_eviction.py` |
| F-10 | Vector search in DuckDB | `storage.py` | `tests/unit/test_vector_search.py` |
| F-11 | Multiple backends via config | `llm/`, `search.py` | `tests/integration/test_search_backends.py` |
| F-12 | Multiple reasoning modes | `orchestration/reasoning.py` | `tests/unit/test_reasoning_modes.py` |
| F-13 | Structured logging (no secrets) | `logging_utils.py` | `tests/unit/test_logging_utils.py` |
| F-14 | Clear errors and config validation | `config.py` | `tests/unit/test_config_reload.py` |
| F-15 | Test coverage for modules | `tests/` | all |
| F-16 | Extensible plugin architecture | `agents/registry.py` | `tests/unit/test_agents_llm.py` |
| F-17 | Adaptive CLI output | `output_format.py` | `tests/unit/test_output_format.py`, `tests/behavior/features/output_formatting.feature` |
| F-18 | Accessibility of output | `output_format.py` | manual review |
| F-19 | Local directory search | `search_backends/local_files.py` | `tests/unit/test_local_search.py`, `tests/behavior/features/local_file_search.feature` |
| F-20 | Local Git repository search by path | `search_backends/local_git.py` | `tests/unit/test_git_search.py`, `tests/behavior/features/git_repository_search.feature` |
