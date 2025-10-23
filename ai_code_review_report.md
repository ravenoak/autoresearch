# AI Code Review Report
Generated: 2025-10-22 14:21:50.853266
Overall Score: 74.5/100

## Summary
- Medium: 451
- Style: 142
- Documentation: 384
- Low: 109
- Security: 34

## Medium Issues
### Style: Import sections not in correct order (stdlib, third-party, local)
**File:** `scripts/check_spec_tests.py`
**Line:** 7
**Suggestion:** Reorder imports: standard library, third-party, then local imports

### Documentation: Public function missing docstring
**File:** `scripts/check_spec_tests.py`
**Line:** 81
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def main() -> int:`

### Style: Import sections not in correct order (stdlib, third-party, local)
**File:** `src/autoresearch/distributed/broker.py`
**Line:** 1
**Suggestion:** Reorder imports: standard library, third-party, then local imports

### Documentation: Public function missing docstring
**File:** `src/autoresearch/distributed/broker.py`
**Line:** 82
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def put(self, item: BrokerMessage) -> None:`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/distributed/broker.py`
**Line:** 87
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def get(self) -> BrokerMessage:`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/distributed/broker.py`
**Line:** 93
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def empty(self) -> bool:  # pragma: no cover - trivial`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/distributed/broker.py`
**Line:** 96
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def close(self) -> None:`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/distributed/broker.py`
**Line:** 99
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def join_thread(self) -> None:`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/distributed/broker.py`
**Line:** 123
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def put(self, item: BrokerMessage) -> None: ...`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/distributed/broker.py`
**Line:** 125
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def get(self) -> BrokerMessage: ...`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/distributed/broker.py`
**Line:** 127
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def close(self) -> None: ...`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/distributed/broker.py`
**Line:** 129
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def join_thread(self) -> None: ...`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/distributed/broker.py`
**Line:** 136
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def put(self, item: PersistClaimMessage) -> None: ...`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/distributed/broker.py`
**Line:** 146
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def rpush(self, name: str, *values: Any) -> Any:  # pragma: no cover - thin wrapper`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/distributed/broker.py`
**Line:** 149
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def blpop(`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/distributed/broker.py`
**Line:** 154
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def close(self) -> None:  # pragma: no cover - thin wrapper`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/distributed/broker.py`
**Line:** 165
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def put(self, message: BrokerMessage) -> None:`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/distributed/broker.py`
**Line:** 168
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def get(self) -> BrokerMessage:`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/distributed/broker.py`
**Line:** 178
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def close(self) -> None:  # pragma: no cover - redis connection handles cleanup`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/distributed/broker.py`
**Line:** 182
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def join_thread(self) -> None:  # pragma: no cover - compatibility shim`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/distributed/broker.py`
**Line:** 202
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def publish(self, message: BrokerMessage) -> None:`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/distributed/broker.py`
**Line:** 205
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def shutdown(self) -> None:`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/distributed/broker.py`
**Line:** 215
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def put(self, message: BrokerMessage) -> None:`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/distributed/broker.py`
**Line:** 218
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def get(self) -> BrokerMessage:`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/distributed/broker.py`
**Line:** 224
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def close(self) -> None:`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/distributed/broker.py`
**Line:** 228
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def join_thread(self) -> None:  # pragma: no cover - Ray queues are remote actors`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/distributed/broker.py`
**Line:** 245
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def publish(self, message: BrokerMessage) -> None:`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/distributed/broker.py`
**Line:** 248
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def shutdown(self) -> None:`

### Style: Import sections not in correct order (stdlib, third-party, local)
**File:** `src/autoresearch/main/app.py`
**Line:** 1
**Suggestion:** Reorder imports: standard library, third-party, then local imports

### Documentation: Public function missing docstring
**File:** `src/autoresearch/main/app.py`
**Line:** 319
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def manifest_add(`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/main/app.py`
**Line:** 383
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def manifest_update(`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/main/app.py`
**Line:** 530
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def workspace_create(`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/main/app.py`
**Line:** 558
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def workspace_select(`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/main/app.py`
**Line:** 575
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def workspace_debate(`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/main/app.py`
**Line:** 623
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def workspace_papers_search(`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/main/app.py`
**Line:** 644
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def workspace_papers_list(`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/main/app.py`
**Line:** 670
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def workspace_papers_ingest(`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/main/app.py`
**Line:** 712
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def workspace_papers_attach(`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/main/app.py`
**Line:** 791
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def start_watcher(`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/main/app.py`
**Line:** 986
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def search(`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/main/app.py`
**Line:** 1169
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def on_cycle_end(loop: int, state: Any) -> None:`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/main/app.py`
**Line:** 1523
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def search_callback(`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/main/app.py`
**Line:** 1747
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def reverify(`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/main/app.py`
**Line:** 1832
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def serve(`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/main/app.py`
**Line:** 1877
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def serve_a2a(`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/main/app.py`
**Line:** 1962
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def completion(`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/main/app.py`
**Line:** 2057
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def capabilities(`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/main/app.py`
**Line:** 2188
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def test_mcp(`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/main/app.py`
**Line:** 2245
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def test_a2a(`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/main/app.py`
**Line:** 2305
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def visualize(`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/main/app.py`
**Line:** 2346
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def visualize_rdf_cli(`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/main/app.py`
**Line:** 2361
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def sparql_query(`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/main/app.py`
**Line:** 2419
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def gui(`

### Style: Import sections not in correct order (stdlib, third-party, local)
**File:** `src/autoresearch/main/config_cli.py`
**Line:** 1
**Suggestion:** Reorder imports: standard library, third-party, then local imports

### Documentation: Public function missing docstring
**File:** `src/autoresearch/main/config_cli.py`
**Line:** 69
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def storage_namespaces(`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/main/config_cli.py`
**Line:** 188
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def config_init(`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/main/config_cli.py`
**Line:** 268
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def config_reasoning(`

### Style: Import sections not in correct order (stdlib, third-party, local)
**File:** `src/autoresearch/orchestration/execution.py`
**Line:** 1
**Suggestion:** Reorder imports: standard library, third-party, then local imports

### Style: Import sections not in correct order (stdlib, third-party, local)
**File:** `src/autoresearch/orchestration/metrics.py`
**Line:** 8
**Suggestion:** Reorder imports: standard library, third-party, then local imports

### Documentation: Public function missing docstring
**File:** `src/autoresearch/orchestration/metrics.py`
**Line:** 441
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def snapshot_reasoning_claims(`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/orchestration/metrics.py`
**Line:** 871
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def request_model_escalation(`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/orchestration/metrics.py`
**Line:** 943
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def record_graph_build(`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/orchestration/metrics.py`
**Line:** 1264
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def get_agent_usage_stats(`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/orchestration/metrics.py`
**Line:** 1293
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def apply_model_routing(`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/orchestration/metrics.py`
**Line:** 1484
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def compress_prompt_if_needed(`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/orchestration/metrics.py`
**Line:** 1574
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def record_context_utilization(`

### Style: Import sections not in correct order (stdlib, third-party, local)
**File:** `src/autoresearch/orchestration/workspace.py`
**Line:** 3
**Suggestion:** Reorder imports: standard library, third-party, then local imports

### Documentation: Public function missing docstring
**File:** `src/autoresearch/orchestration/workspace.py`
**Line:** 42
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def run_query(`

### Style: Import sections not in correct order (stdlib, third-party, local)
**File:** `src/autoresearch/resources/scholarly/fetchers.py`
**Line:** 3
**Suggestion:** Reorder imports: standard library, third-party, then local imports

### Documentation: Public function missing docstring
**File:** `src/autoresearch/resources/scholarly/fetchers.py`
**Line:** 37
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def search(`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/resources/scholarly/fetchers.py`
**Line:** 91
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def search(`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/resources/scholarly/fetchers.py`
**Line:** 107
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def fetch(self, identifier: str) -> PaperDocument:`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/resources/scholarly/fetchers.py`
**Line:** 171
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def search(`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/resources/scholarly/fetchers.py`
**Line:** 192
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def fetch(self, identifier: str) -> PaperDocument:`

### Style: Import sections not in correct order (stdlib, third-party, local)
**File:** `src/autoresearch/resources/scholarly/models.py`
**Line:** 3
**Suggestion:** Reorder imports: standard library, third-party, then local imports

### Style: Import sections not in correct order (stdlib, third-party, local)
**File:** `src/autoresearch/search/core.py`
**Line:** 29
**Suggestion:** Reorder imports: standard library, third-party, then local imports

### Documentation: Public function missing docstring
**File:** `src/autoresearch/search/core.py`
**Line:** 478
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def from_object(cls, obj: Any) -> "_ContextAwareConfig":`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/search/core.py`
**Line:** 493
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def from_object(cls, obj: Any) -> "_LocalFileConfig":`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/search/core.py`
**Line:** 509
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def from_object(cls, obj: Any) -> "_LocalGitConfig":`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/search/core.py`
**Line:** 528
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def from_object(cls, obj: Any) -> "_QueryRewriteConfig":`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/search/core.py`
**Line:** 553
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def from_object(cls, obj: Any) -> "_AdaptiveKConfig":`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/search/core.py`
**Line:** 594
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def from_object(cls, obj: Any) -> "_SearchConfig":`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/search/core.py`
**Line:** 646
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def from_object(cls, obj: Any) -> "_Config":`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/search/core.py`
**Line:** 766
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def class_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/search/core.py`
**Line:** 781
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def instance_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/search/core.py`
**Line:** 1558
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def calculate_semantic_similarity(`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/search/core.py`
**Line:** 1667
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def add_embeddings(`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/search/core.py`
**Line:** 1861
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def merge_rank_scores(`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/search/core.py`
**Line:** 1892
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def merge_semantic_scores(`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/search/core.py`
**Line:** 1919
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def rank_results(`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/search/core.py`
**Line:** 2095
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def cross_backend_rank(`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/search/core.py`
**Line:** 2144
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def embedding_lookup(`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/search/core.py`
**Line:** 2205
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def storage_hybrid_lookup(`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/search/core.py`
**Line:** 2455
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def evaluate_weights(`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/search/core.py`
**Line:** 2476
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def tune_weights(`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/search/core.py`
**Line:** 2496
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def optimize_weights(`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/search/core.py`
**Line:** 2506
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def register_backend(cls, name: str) -> Callable[`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/search/core.py`
**Line:** 2526
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def custom_search(query: str, max_results: int = 5) -> List[Dict[str, str]]:`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/search/core.py`
**Line:** 2531
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def decorator(`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/search/core.py`
**Line:** 2547
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def register_embedding_backend(cls, name: str) -> Callable[`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/search/core.py`
**Line:** 2553
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def decorator(`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/search/core.py`
**Line:** 2621
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def external_lookup(`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/search/core.py`
**Line:** 2854
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def run_backend(name: str) -> Tuple[str, List[Dict[str, Any]]]:`

### Style: Import sections not in correct order (stdlib, third-party, local)
**File:** `src/autoresearch/storage.py`
**Line:** 27
**Suggestion:** Reorder imports: standard library, third-party, then local imports

### Documentation: Public function missing docstring
**File:** `src/autoresearch/storage.py`
**Line:** 179
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def setup(db_path: Optional[str], context: StorageContext) -> StorageContext: ...`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/storage.py`
**Line:** 182
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def teardown(remove_db: bool, context: StorageContext, state: "StorageState") -> None: ...`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/storage.py`
**Line:** 185
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def record_claim_audit(`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/storage.py`
**Line:** 191
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def list_claim_audits(`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/storage.py`
**Line:** 197
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def update_knowledge_graph(`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/storage.py`
**Line:** 206
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def save_workspace_manifest(`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/storage.py`
**Line:** 213
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def save_scholarly_paper(record: JSONMapping) -> JSONDict: ...`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/storage.py`
**Line:** 216
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def list_scholarly_papers(`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/storage.py`
**Line:** 222
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def get_scholarly_paper(`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/storage.py`
**Line:** 229
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def get_workspace_manifest(`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/storage.py`
**Line:** 236
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def list_workspace_manifests(`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/storage.py`
**Line:** 240
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def merge_claim_groups(`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/storage.py`
**Line:** 245
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def persist_claim(`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/storage.py`
**Line:** 251
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def update_claim(`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/storage.py`
**Line:** 257
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def get_claim(`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/storage.py`
**Line:** 263
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def update_rdf_claim(`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/storage.py`
**Line:** 270
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def create_hnsw_index(`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/storage.py`
**Line:** 274
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def refresh_vector_index(`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/storage.py`
**Line:** 508
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def from_score(`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/storage.py`
**Line:** 781
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def setup(`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/storage.py`
**Line:** 844
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def initialize_storage(`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/storage.py`
**Line:** 899
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def teardown(`

### Documentation: Public class missing docstring
**File:** `src/autoresearch/storage.py`
**Line:** 983
**Suggestion:** Add a comprehensive docstring explaining purpose and key methods
**Code:** `class StorageManagerMeta(type):`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/storage.py`
**Line:** 987
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def context(cls) -> StorageContext:`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/storage.py`
**Line:** 991
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def context(cls, value: StorageContext) -> None:`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/storage.py`
**Line:** 1090
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def setup(`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/storage.py`
**Line:** 1127
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def teardown(`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/storage.py`
**Line:** 1150
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def record_claim_audit(`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/storage.py`
**Line:** 1167
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def list_claim_audits(`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/storage.py`
**Line:** 1187
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def save_workspace_manifest(`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/storage.py`
**Line:** 1204
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def get_workspace_manifest(`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/storage.py`
**Line:** 1230
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def list_workspace_manifests(`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/storage.py`
**Line:** 1279
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def list_scholarly_papers(`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/storage.py`
**Line:** 1299
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def get_scholarly_paper(`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/storage.py`
**Line:** 2116
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def update_knowledge_graph(`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/storage.py`
**Line:** 2302
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def merge_claim_groups(`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/storage.py`
**Line:** 2420
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def persist_claim(`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/storage.py`
**Line:** 2598
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def update_claim(`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/storage.py`
**Line:** 2648
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def get_claim(`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/storage.py`
**Line:** 2698
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def update_rdf_claim(`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/storage.py`
**Line:** 2712
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def create_hnsw_index(`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/storage.py`
**Line:** 2743
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def refresh_vector_index(`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/storage.py`
**Line:** 2823
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def vector_search(`

### Documentation: Public class missing docstring
**File:** `src/autoresearch/storage.py`
**Line:** 3108
**Suggestion:** Add a comprehensive docstring explaining purpose and key methods
**Code:** `class name when no explicit identifier is present.`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/storage.py`
**Line:** 3287
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def record(self, key: str) -> str | None:`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/storage.py`
**Line:** 3303
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def record(self, key: str) -> str | None:`

### Style: Import sections not in correct order (stdlib, third-party, local)
**File:** `src/autoresearch/storage_backends.py`
**Line:** 8
**Suggestion:** Reorder imports: standard library, third-party, then local imports

### Documentation: Public function missing docstring
**File:** `src/autoresearch/storage_backends.py`
**Line:** 818
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def persist_graph_entities(`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/storage_backends.py`
**Line:** 858
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def persist_graph_relations(`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/storage_backends.py`
**Line:** 902
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def update_claim(`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/storage_backends.py`
**Line:** 982
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def persist_claim_audit(`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/storage_backends.py`
**Line:** 1074
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def list_claim_audits(`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/storage_backends.py`
**Line:** 1317
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def list_scholarly_papers(`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/storage_backends.py`
**Line:** 1389
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def get_workspace_manifest(`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/storage_backends.py`
**Line:** 1496
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def vector_search(`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/storage_backends.py`
**Line:** 1809
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def setup(self, db_path: str | None = None) -> None:`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/storage_backends.py`
**Line:** 1830
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def close(self) -> None:`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/storage_backends.py`
**Line:** 1835
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def execute(self, query: str, params: dict[str, Any] | None = None) -> "kuzu.QueryResult":`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/storage_backends.py`
**Line:** 1844
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def persist_claim(self, claim: dict[str, Any]) -> None:`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/storage_backends.py`
**Line:** 1856
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def get_claim(self, claim_id: str) -> dict[str, Any]:`

### Security: Potential SQL injection vulnerability
**File:** `src/autoresearch/storage_backends.py`
**Line:** 441
**Suggestion:** Use parameterized queries or prepared statements
**Code:** `self._conn.execute(`

### Security: Potential SQL injection vulnerability
**File:** `src/autoresearch/storage_backends.py`
**Line:** 445
**Suggestion:** Use parameterized queries or prepared statements
**Code:** `self._conn.execute(`

### Security: Potential SQL injection vulnerability
**File:** `src/autoresearch/storage_backends.py`
**Line:** 676
**Suggestion:** Use parameterized queries or prepared statements
**Code:** `rows = self._conn.execute(`

### Security: Potential SQL injection vulnerability
**File:** `src/autoresearch/storage_backends.py`
**Line:** 688
**Suggestion:** Use parameterized queries or prepared statements
**Code:** `self._conn.execute(`

### Security: Potential SQL injection vulnerability
**File:** `src/autoresearch/storage_backends.py`
**Line:** 698
**Suggestion:** Use parameterized queries or prepared statements
**Code:** `self._conn.execute(`

### Security: Potential SQL injection vulnerability
**File:** `src/autoresearch/storage_backends.py`
**Line:** 714
**Suggestion:** Use parameterized queries or prepared statements
**Code:** `self._conn.execute(f"SET hnsw_ef_search={ef_search}")`

### Security: Potential SQL injection vulnerability
**File:** `src/autoresearch/storage_backends.py`
**Line:** 721
**Suggestion:** Use parameterized queries or prepared statements
**Code:** `self._conn.execute(`

### Security: Potential SQL injection vulnerability
**File:** `src/autoresearch/storage_backends.py`
**Line:** 760
**Suggestion:** Use parameterized queries or prepared statements
**Code:** `self._conn.execute(f"DROP INDEX IF EXISTS {index_name}")`

### Security: Potential SQL injection vulnerability
**File:** `src/autoresearch/storage_backends.py`
**Line:** 788
**Suggestion:** Use parameterized queries or prepared statements
**Code:** `conn.execute(`

### Security: Potential SQL injection vulnerability
**File:** `src/autoresearch/storage_backends.py`
**Line:** 799
**Suggestion:** Use parameterized queries or prepared statements
**Code:** `conn.execute(`

### Security: Potential SQL injection vulnerability
**File:** `src/autoresearch/storage_backends.py`
**Line:** 811
**Suggestion:** Use parameterized queries or prepared statements
**Code:** `conn.execute(`

### Security: Potential SQL injection vulnerability
**File:** `src/autoresearch/storage_backends.py`
**Line:** 849
**Suggestion:** Use parameterized queries or prepared statements
**Code:** `conn.execute(f"DELETE FROM {tables.kg_entities} WHERE id=?", [row[0]])`

### Security: Potential SQL injection vulnerability
**File:** `src/autoresearch/storage_backends.py`
**Line:** 851
**Suggestion:** Use parameterized queries or prepared statements
**Code:** `conn.execute(`

### Security: Potential SQL injection vulnerability
**File:** `src/autoresearch/storage_backends.py`
**Line:** 889
**Suggestion:** Use parameterized queries or prepared statements
**Code:** `conn.execute(`

### Security: Potential SQL injection vulnerability
**File:** `src/autoresearch/storage_backends.py`
**Line:** 895
**Suggestion:** Use parameterized queries or prepared statements
**Code:** `conn.execute(`

### Security: Potential SQL injection vulnerability
**File:** `src/autoresearch/storage_backends.py`
**Line:** 925
**Suggestion:** Use parameterized queries or prepared statements
**Code:** `conn.execute(`

### Security: Potential SQL injection vulnerability
**File:** `src/autoresearch/storage_backends.py`
**Line:** 937
**Suggestion:** Use parameterized queries or prepared statements
**Code:** `conn.execute(`

### Security: Potential SQL injection vulnerability
**File:** `src/autoresearch/storage_backends.py`
**Line:** 942
**Suggestion:** Use parameterized queries or prepared statements
**Code:** `conn.execute(`

### Security: Potential SQL injection vulnerability
**File:** `src/autoresearch/storage_backends.py`
**Line:** 947
**Suggestion:** Use parameterized queries or prepared statements
**Code:** `conn.execute(`

### Security: Potential SQL injection vulnerability
**File:** `src/autoresearch/storage_backends.py`
**Line:** 953
**Suggestion:** Use parameterized queries or prepared statements
**Code:** `conn.execute(`

### Security: Potential SQL injection vulnerability
**File:** `src/autoresearch/storage_backends.py`
**Line:** 958
**Suggestion:** Use parameterized queries or prepared statements
**Code:** `conn.execute(`

### Security: Potential SQL injection vulnerability
**File:** `src/autoresearch/storage_backends.py`
**Line:** 969
**Suggestion:** Use parameterized queries or prepared statements
**Code:** `conn.execute(`

### Security: Potential SQL injection vulnerability
**File:** `src/autoresearch/storage_backends.py`
**Line:** 975
**Suggestion:** Use parameterized queries or prepared statements
**Code:** `conn.execute(`

### Security: Potential SQL injection vulnerability
**File:** `src/autoresearch/storage_backends.py`
**Line:** 1059
**Suggestion:** Use parameterized queries or prepared statements
**Code:** `conn.execute(`

### Security: Potential SQL injection vulnerability
**File:** `src/autoresearch/storage_backends.py`
**Line:** 1297
**Suggestion:** Use parameterized queries or prepared statements
**Code:** `self._conn.execute(`

### Security: Potential SQL injection vulnerability
**File:** `src/autoresearch/storage_backends.py`
**Line:** 1473
**Suggestion:** Use parameterized queries or prepared statements
**Code:** `row = conn.execute(`

### Security: Potential SQL injection vulnerability
**File:** `src/autoresearch/storage_backends.py`
**Line:** 1485
**Suggestion:** Use parameterized queries or prepared statements
**Code:** `emb = conn.execute(`

### Security: Potential SQL injection vulnerability
**File:** `src/autoresearch/storage_backends.py`
**Line:** 1557
**Suggestion:** Use parameterized queries or prepared statements
**Code:** `self._conn.execute(f"SET hnsw_ef_search={ef_search}")`

### Security: Potential SQL injection vulnerability
**File:** `src/autoresearch/storage_backends.py`
**Line:** 1561
**Suggestion:** Use parameterized queries or prepared statements
**Code:** `self._conn.execute(f"SET vss_search_batch_size={cfg.vector_search_batch_size}")`

### Security: Potential SQL injection vulnerability
**File:** `src/autoresearch/storage_backends.py`
**Line:** 1665
**Suggestion:** Use parameterized queries or prepared statements
**Code:** `self._conn.execute(f"SET query_timeout_ms={cfg.vector_search_timeout_ms}")`

### Security: Potential SQL injection vulnerability
**File:** `src/autoresearch/storage_backends.py`
**Line:** 1793
**Suggestion:** Use parameterized queries or prepared statements
**Code:** `self._conn.execute(f"DELETE FROM {tables.kg_entities}")`

### Security: Potential SQL injection vulnerability
**File:** `src/autoresearch/storage_backends.py`
**Line:** 1794
**Suggestion:** Use parameterized queries or prepared statements
**Code:** `self._conn.execute(f"DELETE FROM {tables.kg_relations}")`

### Security: Potential SQL injection vulnerability
**File:** `src/autoresearch/storage_backends.py`
**Line:** 1847
**Suggestion:** Use parameterized queries or prepared statements
**Code:** `self.execute(`

### Security: Potential SQL injection vulnerability
**File:** `src/autoresearch/storage_backends.py`
**Line:** 1859
**Suggestion:** Use parameterized queries or prepared statements
**Code:** `res = self.execute(`

### Style: Import sections not in correct order (stdlib, third-party, local)
**File:** `src/autoresearch/storage_utils.py`
**Line:** 3
**Suggestion:** Reorder imports: standard library, third-party, then local imports

### Documentation: Public function missing docstring
**File:** `src/autoresearch/storage_utils.py`
**Line:** 34
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def from_any(`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/storage_utils.py`
**Line:** 126
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def resolve_namespace(`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/storage_utils.py`
**Line:** 204
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def graph_subject_objects(`

### Style: Import sections not in correct order (stdlib, third-party, local)
**File:** `src/autoresearch/ui/desktop/__init__.py`
**Line:** 15
**Suggestion:** Reorder imports: standard library, third-party, then local imports

### Style: Import sections not in correct order (stdlib, third-party, local)
**File:** `src/autoresearch/ui/desktop/knowledge_graph_view.py`
**Line:** 3
**Suggestion:** Reorder imports: standard library, third-party, then local imports

### Style: Import sections not in correct order (stdlib, third-party, local)
**File:** `src/autoresearch/ui/desktop/main.py`
**Line:** 8
**Suggestion:** Reorder imports: standard library, third-party, then local imports

### Style: Import sections not in correct order (stdlib, third-party, local)
**File:** `src/autoresearch/ui/desktop/main_window.py`
**Line:** 8
**Suggestion:** Reorder imports: standard library, third-party, then local imports

### Documentation: Public function missing docstring
**File:** `src/autoresearch/ui/desktop/main_window.py`
**Line:** 504
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def on_workspace_selected(`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/ui/desktop/main_window.py`
**Line:** 576
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def on_workspace_debate_requested(`

### Documentation: Public class missing docstring
**File:** `src/autoresearch/ui/desktop/main_window.py`
**Line:** 875
**Suggestion:** Add a comprehensive docstring explaining purpose and key methods
**Code:** `class QueryWorker(QRunnable):`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/ui/desktop/main_window.py`
**Line:** 893
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def run(self):`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/ui/desktop/main_window.py`
**Line:** 930
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def display_results(`

### Style: Import sections not in correct order (stdlib, third-party, local)
**File:** `src/autoresearch/ui/desktop/metrics_dashboard.py`
**Line:** 3
**Suggestion:** Reorder imports: standard library, third-party, then local imports

### Documentation: Public function missing docstring
**File:** `src/autoresearch/ui/desktop/metrics_dashboard.py`
**Line:** 150
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def bind_metrics_provider(`

### Style: Import sections not in correct order (stdlib, third-party, local)
**File:** `src/autoresearch/ui/desktop/query_panel.py`
**Line:** 8
**Suggestion:** Reorder imports: standard library, third-party, then local imports

### Style: Import sections not in correct order (stdlib, third-party, local)
**File:** `src/autoresearch/ui/desktop/results_table.py`
**Line:** 3
**Suggestion:** Reorder imports: standard library, third-party, then local imports

### Documentation: Public function missing docstring
**File:** `src/autoresearch/ui/desktop/results_table.py`
**Line:** 41
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: D401 - Qt signature  # type: ignore[override]`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/ui/desktop/results_table.py`
**Line:** 46
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: D401 - Qt signature  # type: ignore[override]`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/ui/desktop/results_table.py`
**Line:** 51
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:  # noqa: D401 - Qt signature  # type: ignore[override]`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/ui/desktop/results_table.py`
**Line:** 71
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def headerData(`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/ui/desktop/results_table.py`
**Line:** 88
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def flags(self, index: QModelIndex) -> Qt.ItemFlags:  # noqa: D401 - Qt signature  # type: ignore[override]`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/ui/desktop/results_table.py`
**Line:** 151
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def model(self) -> SearchResultsModel:`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/ui/desktop/results_table.py`
**Line:** 156
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def setModel(self, model: QAbstractTableModel) -> None:  # noqa: N802 - Qt override  # type: ignore[override]`

### Style: Import sections not in correct order (stdlib, third-party, local)
**File:** `src/autoresearch/ui/desktop/session_manager.py`
**Line:** 3
**Suggestion:** Reorder imports: standard library, third-party, then local imports

### Documentation: Public function missing docstring
**File:** `src/autoresearch/ui/desktop/session_manager.py`
**Line:** 109
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def add_workspace(`

### Style: Import sections not in correct order (stdlib, third-party, local)
**File:** `src/autoresearch/ui/tui/dashboard.py`
**Line:** 3
**Suggestion:** Reorder imports: standard library, third-party, then local imports

### Documentation: Public function missing docstring
**File:** `src/autoresearch/ui/tui/dashboard.py`
**Line:** 200
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def complete_cycle(`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/ui/tui/dashboard.py`
**Line:** 246
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def run_dashboard(`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/ui/tui/dashboard.py`
**Line:** 299
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def compose(self) -> ComposeResult:`

### Documentation: Public function missing docstring
**File:** `src/autoresearch/ui/tui/dashboard.py`
**Line:** 308
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def on_mount(self) -> None:`

### Documentation: Public function missing docstring
**File:** `tests/behavior/archive/test_cleanup_steps.py`
**Line:** 63
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def system_configured_with_multiple_agents(`

### Documentation: Public function missing docstring
**File:** `tests/behavior/archive/test_cleanup_steps.py`
**Line:** 81
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def run_query_with_dialectical_reasoning(`

### Documentation: Public function missing docstring
**File:** `tests/behavior/archive/test_cleanup_steps.py`
**Line:** 98
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def get_agent(name: str) -> MagicMock:`

### Style: Import sections not in correct order (stdlib, third-party, local)
**File:** `tests/behavior/steps/dkg_persistence_steps.py`
**Line:** 45
**Suggestion:** Reorder imports: standard library, third-party, then local imports

### Documentation: Public function missing docstring
**File:** `tests/behavior/steps/dkg_persistence_steps.py`
**Line:** 52
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def mock_ensure_storage_initialized():`

### Documentation: Public function missing docstring
**File:** `tests/behavior/steps/dkg_persistence_steps.py`
**Line:** 66
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def restore():`

### Documentation: Public function missing docstring
**File:** `tests/behavior/steps/dkg_persistence_steps.py`
**Line:** 92
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def agent_asserts_claim(valid_claim):`

### Documentation: Public function missing docstring
**File:** `tests/behavior/steps/dkg_persistence_steps.py`
**Line:** 264
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def try_persist_valid_claim_uninit(`

### Documentation: Public function missing docstring
**File:** `tests/behavior/steps/dkg_persistence_steps.py`
**Line:** 387
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def load_subclass_ontology(tmp_path):`

### Documentation: Public function missing docstring
**File:** `tests/behavior/steps/dkg_persistence_steps.py`
**Line:** 402
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def add_subclass_instance():`

### Documentation: Public function missing docstring
**File:** `tests/behavior/steps/dkg_persistence_steps.py`
**Line:** 417
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def apply_reasoning(monkeypatch):`

### Documentation: Public function missing docstring
**File:** `tests/behavior/steps/dkg_persistence_steps.py`
**Line:** 439
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def check_superclass_query():`

### Documentation: Public function missing docstring
**File:** `tests/behavior/steps/dkg_persistence_steps.py`
**Line:** 447
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def add_simple_triple():`

### Documentation: Public function missing docstring
**File:** `tests/behavior/steps/dkg_persistence_steps.py`
**Line:** 462
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def visualize_graph(tmp_path, file):`

### Documentation: Public function missing docstring
**File:** `tests/behavior/steps/dkg_persistence_steps.py`
**Line:** 471
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def check_visualization(tmp_path, file, viz_path):`

### Style: Import sections not in correct order (stdlib, third-party, local)
**File:** `tests/behavior/steps/gui_history_steps.py`
**Line:** 4
**Suggestion:** Reorder imports: standard library, third-party, then local imports

### Documentation: Public function missing docstring
**File:** `tests/behavior/steps/gui_history_steps.py`
**Line:** 20
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def streamlit_app_with_history(monkeypatch, tmp_path, bdd_context: BehaviorContext):`

### Documentation: Public function missing docstring
**File:** `tests/behavior/steps/gui_history_steps.py`
**Line:** 33
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def fake_store(query, result, config):`

### Documentation: Public function missing docstring
**File:** `tests/behavior/steps/gui_history_steps.py`
**Line:** 66
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def view_query_history(bdd_context: BehaviorContext):`

### Documentation: Public function missing docstring
**File:** `tests/behavior/steps/gui_history_steps.py`
**Line:** 70
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def fake_form(*args, **kwargs):`

### Documentation: Public function missing docstring
**File:** `tests/behavior/steps/gui_history_steps.py`
**Line:** 86
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def previous_query_visible(bdd_context: BehaviorContext):`

### Documentation: Public function missing docstring
**File:** `tests/behavior/steps/gui_history_steps.py`
**Line:** 93
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def rerun_query_from_history(bdd_context: BehaviorContext):`

### Documentation: Public function missing docstring
**File:** `tests/behavior/steps/gui_history_steps.py`
**Line:** 97
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def fake_form(*args, **kwargs):`

### Documentation: Public function missing docstring
**File:** `tests/behavior/steps/gui_history_steps.py`
**Line:** 127
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def rerun_matches_original(bdd_context: BehaviorContext):`

### Style: Import sections not in correct order (stdlib, third-party, local)
**File:** `tests/behavior/steps/scholarly_steps.py`
**Line:** 1
**Suggestion:** Reorder imports: standard library, third-party, then local imports

### Documentation: Public function missing docstring
**File:** `tests/behavior/steps/scholarly_steps.py`
**Line:** 23
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def fetch_paper_fixture(`

### Documentation: Public function missing docstring
**File:** `tests/behavior/steps/scholarly_steps.py`
**Line:** 45
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def assert_cache_metadata(bdd_context: BehaviorContext) -> None:`

### Documentation: Public function missing docstring
**File:** `tests/behavior/steps/scholarly_steps.py`
**Line:** 54
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def simulate_offline(bdd_context: BehaviorContext) -> None:`

### Documentation: Public function missing docstring
**File:** `tests/behavior/steps/scholarly_steps.py`
**Line:** 59
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def load_cached_content(question: str, bdd_context: BehaviorContext) -> None:`

### Documentation: Public function missing docstring
**File:** `tests/behavior/steps/scholarly_steps.py`
**Line:** 68
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def verify_cached_result(bdd_context: BehaviorContext) -> None:`

### Documentation: Public function missing docstring
**File:** `tests/behavior/steps/scholarly_steps.py`
**Line:** 78
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def verify_cache_timestamp(bdd_context: BehaviorContext) -> None:`

### Documentation: Public function missing docstring
**File:** `tests/behavior/steps/user_workflows_steps.py`
**Line:** 22
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def test_cli_workflow(bdd_context: BehaviorContext):`

### Documentation: Public function missing docstring
**File:** `tests/behavior/steps/user_workflows_steps.py`
**Line:** 30
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def test_cli_workflow_invalid_backend(bdd_context: BehaviorContext):`

### Style: Import sections not in correct order (stdlib, third-party, local)
**File:** `tests/ui/desktop/test_component_smoke.py`
**Line:** 4
**Suggestion:** Reorder imports: standard library, third-party, then local imports

### Documentation: Public function missing docstring
**File:** `tests/ui/desktop/test_component_smoke.py`
**Line:** 51
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def telemetry_events() -> list[tuple[str, Mapping[str, Any]]]:`

### Documentation: Public function missing docstring
**File:** `tests/ui/desktop/test_component_smoke.py`
**Line:** 65
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def test_desktop_telemetry_emits_default_category(monkeypatch) -> None:`

### Documentation: Public function missing docstring
**File:** `tests/ui/desktop/test_component_smoke.py`
**Line:** 68
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def fake_qcinfo(category: Any, message: str) -> None:`

### Documentation: Public function missing docstring
**File:** `tests/ui/desktop/test_component_smoke.py`
**Line:** 82
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def test_knowledge_graph_view_smoke(qtbot) -> None:`

### Documentation: Public function missing docstring
**File:** `tests/ui/desktop/test_component_smoke.py`
**Line:** 90
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def test_metrics_dashboard_smoke(qtbot) -> None:`

### Documentation: Public function missing docstring
**File:** `tests/ui/desktop/test_component_smoke.py`
**Line:** 116
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def test_metrics_dashboard_auto_refresh(qtbot) -> None:`

### Documentation: Public function missing docstring
**File:** `tests/ui/desktop/test_component_smoke.py`
**Line:** 129
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def provider() -> Mapping[str, float | dict[str, float]] | None:`

### Documentation: Public function missing docstring
**File:** `tests/ui/desktop/test_component_smoke.py`
**Line:** 151
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def test_config_editor_smoke(qtbot) -> None:`

### Documentation: Public function missing docstring
**File:** `tests/ui/desktop/test_component_smoke.py`
**Line:** 162
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def test_session_manager_smoke(qtbot) -> None:`

### Documentation: Public function missing docstring
**File:** `tests/ui/desktop/test_component_smoke.py`
**Line:** 172
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def test_export_manager_smoke(qtbot) -> None:`

### Documentation: Public function missing docstring
**File:** `tests/ui/desktop/test_component_smoke.py`
**Line:** 182
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def test_main_window_smoke(qtbot) -> None:`

### Documentation: Public function missing docstring
**File:** `tests/ui/desktop/test_component_smoke.py`
**Line:** 191
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def test_main_window_applies_query_panel_overrides(qtbot, monkeypatch) -> None:`

### Documentation: Public class missing docstring
**File:** `tests/ui/desktop/test_component_smoke.py`
**Line:** 194
**Suggestion:** Add a comprehensive docstring explaining purpose and key methods
**Code:** `class DummyLoader:`

### Documentation: Public function missing docstring
**File:** `tests/ui/desktop/test_component_smoke.py`
**Line:** 195
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def load_config(self) -> ConfigModel:`

### Documentation: Public class missing docstring
**File:** `tests/ui/desktop/test_component_smoke.py`
**Line:** 198
**Suggestion:** Add a comprehensive docstring explaining purpose and key methods
**Code:** `class DummyOrchestrator:`

### Documentation: Public function missing docstring
**File:** `tests/ui/desktop/test_component_smoke.py`
**Line:** 199
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def run_query(self, query: str, config: ConfigModel) -> QueryResponse:`

### Documentation: Public class missing docstring
**File:** `tests/ui/desktop/test_component_smoke.py`
**Line:** 218
**Suggestion:** Add a comprehensive docstring explaining purpose and key methods
**Code:** `class ImmediateThreadPool:`

### Documentation: Public function missing docstring
**File:** `tests/ui/desktop/test_component_smoke.py`
**Line:** 219
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def start(self, worker) -> None:`

### Documentation: Public function missing docstring
**File:** `tests/ui/desktop/test_component_smoke.py`
**Line:** 228
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def immediate_single_shot(_interval: int, receiver, slot=None) -> None:`

### Documentation: Public function missing docstring
**File:** `tests/ui/desktop/test_component_smoke.py`
**Line:** 259
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def test_results_display_citations_tab_and_controls(qtbot) -> None:`

### Documentation: Public function missing docstring
**File:** `tests/ui/desktop/test_component_smoke.py`
**Line:** 298
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def test_results_display_markdown_conversion_handles_rich_content(qtbot) -> None:`

### Documentation: Public class missing docstring
**File:** `tests/ui/desktop/test_component_smoke.py`
**Line:** 321
**Suggestion:** Add a comprehensive docstring explaining purpose and key methods
**Code:** `class ImmediateThreadPool:`

### Documentation: Public function missing docstring
**File:** `tests/ui/desktop/test_component_smoke.py`
**Line:** 322
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def start(self, worker) -> None:`

### Documentation: Public function missing docstring
**File:** `tests/ui/desktop/test_component_smoke.py`
**Line:** 331
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def immediate_single_shot(_interval: int, receiver, slot=None) -> None:`

### Documentation: Public class missing docstring
**File:** `tests/ui/desktop/test_component_smoke.py`
**Line:** 339
**Suggestion:** Add a comprehensive docstring explaining purpose and key methods
**Code:** `class DeferredThreadPool:`

### Documentation: Public function missing docstring
**File:** `tests/ui/desktop/test_component_smoke.py`
**Line:** 343
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def start(self, worker) -> None:`

### Documentation: Public function missing docstring
**File:** `tests/ui/desktop/test_component_smoke.py`
**Line:** 354
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def immediate_single_shot(_interval: int, receiver, slot=None) -> None:`

### Documentation: Public class missing docstring
**File:** `tests/ui/desktop/test_component_smoke.py`
**Line:** 368
**Suggestion:** Add a comprehensive docstring explaining purpose and key methods
**Code:** `class DummyLoader:`

### Documentation: Public function missing docstring
**File:** `tests/ui/desktop/test_component_smoke.py`
**Line:** 369
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def load_config(self) -> ConfigModel:`

### Documentation: Public class missing docstring
**File:** `tests/ui/desktop/test_component_smoke.py`
**Line:** 372
**Suggestion:** Add a comprehensive docstring explaining purpose and key methods
**Code:** `class DummyOrchestrator:`

### Documentation: Public function missing docstring
**File:** `tests/ui/desktop/test_component_smoke.py`
**Line:** 373
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def run_query(self, query: str, config: ConfigModel) -> QueryResponse:`

### Documentation: Public function missing docstring
**File:** `tests/ui/desktop/test_component_smoke.py`
**Line:** 399
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def test_export_buttons_gated_during_query(`

### Documentation: Public function missing docstring
**File:** `tests/ui/desktop/test_component_smoke.py`
**Line:** 449
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def test_main_window_emits_completed_telemetry(`

### Documentation: Public function missing docstring
**File:** `tests/ui/desktop/test_component_smoke.py`
**Line:** 479
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def test_main_window_emits_failed_telemetry(`

### Documentation: Public function missing docstring
**File:** `tests/ui/desktop/test_component_smoke.py`
**Line:** 510
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def test_main_window_emits_cancelled_telemetry(`

### Documentation: Public function missing docstring
**File:** `tests/ui/desktop/test_component_smoke.py`
**Line:** 522
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def fake_question(`

### Documentation: Public function missing docstring
**File:** `tests/ui/desktop/test_component_smoke.py`
**Line:** 579
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def test_main_window_cancel_decline_keeps_worker_running(`

### Documentation: Public function missing docstring
**File:** `tests/ui/desktop/test_component_smoke.py`
**Line:** 591
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def fake_question(`

### Documentation: Public function missing docstring
**File:** `tests/ui/desktop/test_desktop_integration.py`
**Line:** 39
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def start(self, worker) -> None:  # noqa: D401 - Qt-compatible signature`

### Documentation: Public function missing docstring
**File:** `tests/ui/desktop/test_desktop_integration.py`
**Line:** 45
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def singleShot(_interval: int, receiver, slot=None) -> None:  # noqa: D401`

### Documentation: Public function missing docstring
**File:** `tests/ui/desktop/test_desktop_integration.py`
**Line:** 54
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def render(result, output_format: str, *, depth: str = "standard") -> str:`

### Documentation: Public function missing docstring
**File:** `tests/ui/desktop/test_desktop_integration.py`
**Line:** 69
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def test_desktop_main_window_runs_query_end_to_end(qtbot, monkeypatch) -> None:`

### Documentation: Public class missing docstring
**File:** `tests/ui/desktop/test_desktop_integration.py`
**Line:** 73
**Suggestion:** Add a comprehensive docstring explaining purpose and key methods
**Code:** `class DummyConfigLoader:`

### Documentation: Public function missing docstring
**File:** `tests/ui/desktop/test_desktop_integration.py`
**Line:** 74
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def load_config(self) -> ConfigModel:`

### Documentation: Public class missing docstring
**File:** `tests/ui/desktop/test_desktop_integration.py`
**Line:** 77
**Suggestion:** Add a comprehensive docstring explaining purpose and key methods
**Code:** `class DummyOrchestrator:`

### Documentation: Public function missing docstring
**File:** `tests/ui/desktop/test_desktop_integration.py`
**Line:** 78
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def run_query(self, query: str, config: ConfigModel) -> QueryResponse:`

### Documentation: Public function missing docstring
**File:** `tests/ui/desktop/test_query_panel.py`
**Line:** 30
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def test_query_panel_emits_signal_and_updates_configuration(qtbot) -> None:`

### Documentation: Public function missing docstring
**File:** `tests/ui/desktop/test_query_panel.py`
**Line:** 60
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def test_query_panel_supports_keyboard_focus_traversal(qtbot) -> None:`

### Documentation: Public function missing docstring
**File:** `tests/ui/desktop/test_query_panel.py`
**Line:** 85
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def test_query_panel_handles_long_text_without_truncation(qtbot) -> None:`

### Documentation: Public function missing docstring
**File:** `tests/ui/desktop/test_query_panel.py`
**Line:** 104
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def test_query_panel_busy_state_disables_controls_and_restores_focus(qtbot) -> None:`

### Style: Import sections not in correct order (stdlib, third-party, local)
**File:** `tests/ui/desktop/test_results_display.py`
**Line:** 6
**Suggestion:** Reorder imports: standard library, third-party, then local imports

### Documentation: Public function missing docstring
**File:** `tests/ui/desktop/test_results_display.py`
**Line:** 37
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def render(result, output_format: str, *, depth: str = "standard") -> str:`

### Documentation: Public function missing docstring
**File:** `tests/ui/desktop/test_results_display.py`
**Line:** 48
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def test_results_display_renders_views_and_enables_citation_controls(qtbot) -> None:`

### Documentation: Public function missing docstring
**File:** `tests/ui/desktop/test_results_display.py`
**Line:** 63
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def setHtml(self, html: str) -> None:  # noqa: N802 - Qt naming convention`

### Documentation: Public function missing docstring
**File:** `tests/ui/desktop/test_results_display.py`
**Line:** 171
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def test_results_display_handles_missing_citations_gracefully(qtbot) -> None:`

### Documentation: Public function missing docstring
**File:** `tests/ui/desktop/test_results_display.py`
**Line:** 180
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def setHtml(self, html: str) -> None:  # noqa: N802 - Qt naming convention`

### Documentation: Public function missing docstring
**File:** `tests/ui/desktop/test_results_display.py`
**Line:** 225
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def test_results_display_loads_graph_from_storage(monkeypatch, qtbot) -> None:`

### Documentation: Public function missing docstring
**File:** `tests/ui/desktop/test_results_display.py`
**Line:** 232
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def nodes(self):  # noqa: D401 - mimic networkx signature`

### Documentation: Public function missing docstring
**File:** `tests/ui/desktop/test_results_display.py`
**Line:** 235
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def edges(self, keys=False, data=False):  # noqa: D401 - mimic networkx signature`

### Documentation: Public function missing docstring
**File:** `tests/ui/desktop/test_results_display.py`
**Line:** 244
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def get_knowledge_graph(*, create: bool = True):  # noqa: D401 - mimic storage signature`

### Documentation: Public function missing docstring
**File:** `tests/ui/desktop/test_results_display.py`
**Line:** 267
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def test_results_display_uses_graph_json_export(qtbot) -> None:`

### Documentation: Public function missing docstring
**File:** `tests/ui/desktop/test_results_display.py`
**Line:** 290
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def test_results_display_falls_back_without_webengine(monkeypatch, qtbot) -> None:`

### Style: Import sections not in correct order (stdlib, third-party, local)
**File:** `tests/unit/knowledge/test_graph_pipeline.py`
**Line:** 1
**Suggestion:** Reorder imports: standard library, third-party, then local imports

### Documentation: Public class missing docstring
**File:** `tests/unit/knowledge/test_graph_pipeline.py`
**Line:** 14
**Suggestion:** Add a comprehensive docstring explaining purpose and key methods
**Code:** `class DummyBackend:`

### Documentation: Public function missing docstring
**File:** `tests/unit/knowledge/test_graph_pipeline.py`
**Line:** 19
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def persist_graph_entities(self, payload: list[dict[str, Any]]) -> None:`

### Documentation: Public function missing docstring
**File:** `tests/unit/knowledge/test_graph_pipeline.py`
**Line:** 22
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def persist_graph_relations(self, payload: list[dict[str, Any]]) -> None:`

### Documentation: Public class missing docstring
**File:** `tests/unit/knowledge/test_graph_pipeline.py`
**Line:** 26
**Suggestion:** Add a comprehensive docstring explaining purpose and key methods
**Code:** `class DummyRDFStore:`

### Documentation: Public function missing docstring
**File:** `tests/unit/knowledge/test_graph_pipeline.py`
**Line:** 30
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def add(self, triple: tuple[Any, Any, Any]) -> None:`

### Documentation: Public function missing docstring
**File:** `tests/unit/knowledge/test_graph_pipeline.py`
**Line:** 44
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def test_session_graph_pipeline_ingest_records_provenance(monkeypatch: pytest.MonkeyPatch) -> None:`

### Documentation: Public function missing docstring
**File:** `tests/unit/knowledge/test_graph_pipeline.py`
**Line:** 89
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def test_session_graph_pipeline_neighbors_uses_storage(monkeypatch: pytest.MonkeyPatch) -> None:`

### Style: Import sections not in correct order (stdlib, third-party, local)
**File:** `tests/unit/legacy/test_cache.py`
**Line:** 2
**Suggestion:** Reorder imports: standard library, third-party, then local imports

### Documentation: Public function missing docstring
**File:** `tests/unit/legacy/test_cache.py`
**Line:** 44
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def property_search(`

### Documentation: Public function missing docstring
**File:** `tests/unit/legacy/test_cache.py`
**Line:** 107
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def test_search_uses_cache(monkeypatch: pytest.MonkeyPatch) -> None:`

### Documentation: Public function missing docstring
**File:** `tests/unit/legacy/test_cache.py`
**Line:** 119
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def backend(query: str, max_results: int = 5) -> list[dict[str, str]]:`

### Documentation: Public function missing docstring
**File:** `tests/unit/legacy/test_cache.py`
**Line:** 181
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def worker() -> None:`

### Documentation: Public function missing docstring
**File:** `tests/unit/legacy/test_cache.py`
**Line:** 196
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def test_cache_is_backend_specific(monkeypatch: pytest.MonkeyPatch) -> None:`

### Documentation: Public function missing docstring
**File:** `tests/unit/legacy/test_cache.py`
**Line:** 208
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def backend1(query: str, max_results: int = 5) -> list[dict[str, str]]:`

### Documentation: Public function missing docstring
**File:** `tests/unit/legacy/test_cache.py`
**Line:** 212
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def backend2(query: str, max_results: int = 5) -> list[dict[str, str]]:`

### Documentation: Public function missing docstring
**File:** `tests/unit/legacy/test_cache.py`
**Line:** 273
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def test_cache_is_backend_specific_without_embeddings(`

### Documentation: Public function missing docstring
**File:** `tests/unit/legacy/test_cache.py`
**Line:** 297
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def backend1(query: str, max_results: int = 5) -> list[dict[str, str]]:`

### Documentation: Public function missing docstring
**File:** `tests/unit/legacy/test_cache.py`
**Line:** 301
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def backend2(query: str, max_results: int = 5) -> list[dict[str, str]]:`

### Documentation: Public function missing docstring
**File:** `tests/unit/legacy/test_cache.py`
**Line:** 345
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def test_cache_key_normalizes_queries(monkeypatch: pytest.MonkeyPatch) -> None:`

### Documentation: Public function missing docstring
**File:** `tests/unit/legacy/test_cache.py`
**Line:** 362
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def backend(query: str, max_results: int = 5) -> list[dict[str, str]]:`

### Documentation: Public function missing docstring
**File:** `tests/unit/legacy/test_cache.py`
**Line:** 395
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def test_cache_key_respects_embedding_flags(monkeypatch: pytest.MonkeyPatch) -> None:`

### Documentation: Public function missing docstring
**File:** `tests/unit/legacy/test_cache.py`
**Line:** 412
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def backend(query: str, max_results: int = 5) -> list[dict[str, str]]:`

### Documentation: Public function missing docstring
**File:** `tests/unit/legacy/test_cache.py`
**Line:** 450
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def test_legacy_cache_entries_upgrade_on_hit(`

### Documentation: Public function missing docstring
**File:** `tests/unit/legacy/test_cache.py`
**Line:** 470
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def backend(text: str, max_results: int = 5) -> list[dict[str, str]]:`

### Documentation: Public function missing docstring
**File:** `tests/unit/legacy/test_cache.py`
**Line:** 556
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def test_v2_cache_entries_upgrade_on_hit(`

### Documentation: Public function missing docstring
**File:** `tests/unit/legacy/test_cache.py`
**Line:** 566
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def backend(text: str, max_results: int = 5) -> list[dict[str, str]]:`

### Documentation: Public function missing docstring
**File:** `tests/unit/legacy/test_cache.py`
**Line:** 716
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def test_cache_key_primary_reflects_hybrid_flags(`

### Documentation: Public function missing docstring
**File:** `tests/unit/legacy/test_cache.py`
**Line:** 773
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def test_sequential_hybrid_sequences_respect_cache_fingerprint(`

### Documentation: Public function missing docstring
**File:** `tests/unit/legacy/test_cache.py`
**Line:** 783
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def backend_factory(label: str) -> Callable[[str, int], list[dict[str, str]]]:`

### Documentation: Public function missing docstring
**File:** `tests/unit/legacy/test_cache.py`
**Line:** 904
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def test_interleaved_storage_paths_share_cache(`

### Documentation: Public function missing docstring
**File:** `tests/unit/legacy/test_cache.py`
**Line:** 913
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def backend(query: str, max_results: int = 5) -> list[dict[str, str]]:`

### Documentation: Public function missing docstring
**File:** `tests/unit/legacy/test_cache.py`
**Line:** 917
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def duckdb_backend(embedding: np.ndarray, max_results: int = 5) -> list[dict[str, str]]:`

### Documentation: Public function missing docstring
**File:** `tests/unit/legacy/test_cache.py`
**Line:** 961
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def fake_storage(`

### Documentation: Public function missing docstring
**File:** `tests/unit/legacy/test_cache.py`
**Line:** 1009
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def primary_cache_key() -> CacheKey:`

### Documentation: Public function missing docstring
**File:** `tests/unit/legacy/test_cache.py`
**Line:** 1020
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def duckdb_cache_key(query_value: str, hints: tuple[str, ...]) -> CacheKey:`

### Documentation: Public function missing docstring
**File:** `tests/unit/legacy/test_cache.py`
**Line:** 1040
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def unique_slots(`

### Documentation: Public function missing docstring
**File:** `tests/unit/legacy/test_cache.py`
**Line:** 1091
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def event_counter(`

### Documentation: Public function missing docstring
**File:** `tests/unit/legacy/test_cache.py`
**Line:** 1234
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def test_context_aware_query_expansion_uses_cache(`

### Documentation: Public function missing docstring
**File:** `tests/unit/legacy/test_cache.py`
**Line:** 1248
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def backend(query: str, max_results: int = 5) -> list[dict[str, str]]:`

### Documentation: Public class missing docstring
**File:** `tests/unit/legacy/test_cache.py`
**Line:** 1252
**Suggestion:** Add a comprehensive docstring explaining purpose and key methods
**Code:** `class DummyContext:`

### Documentation: Public function missing docstring
**File:** `tests/unit/legacy/test_cache.py`
**Line:** 1253
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def expand_query(self, query: str) -> str:`

### Documentation: Public function missing docstring
**File:** `tests/unit/legacy/test_cache.py`
**Line:** 1256
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def add_to_history(`

### Documentation: Public function missing docstring
**File:** `tests/unit/legacy/test_cache.py`
**Line:** 1261
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def build_topic_model(self) -> None:  # pragma: no cover - no-op`

### Documentation: Public function missing docstring
**File:** `tests/unit/legacy/test_cache.py`
**Line:** 1264
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def reset_search_strategy(self) -> None:  # pragma: no cover - no-op`

### Documentation: Public function missing docstring
**File:** `tests/unit/legacy/test_cache.py`
**Line:** 1267
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def summarize_retrieval_outcome(`

### Documentation: Public function missing docstring
**File:** `tests/unit/legacy/test_cache.py`
**Line:** 1283
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def record_fetch_plan(self, *args: object, **kwargs: object) -> None:  # pragma: no cover`

### Documentation: Public function missing docstring
**File:** `tests/unit/legacy/test_cache.py`
**Line:** 1286
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def record_scout_observation(`

### Style: Import sections not in correct order (stdlib, third-party, local)
**File:** `tests/unit/legacy/test_cli_gui_env_gate.py`
**Line:** 2
**Suggestion:** Reorder imports: standard library, third-party, then local imports

### Documentation: Public function missing docstring
**File:** `tests/unit/legacy/test_cli_gui_env_gate.py`
**Line:** 11
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def test_gui_requires_opt_in(monkeypatch):`

### Documentation: Public function missing docstring
**File:** `tests/unit/legacy/test_cli_gui_env_gate.py`
**Line:** 36
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def test_gui_runs_with_opt_in(monkeypatch):`

### Documentation: Public function missing docstring
**File:** `tests/unit/legacy/test_cli_gui_env_gate.py`
**Line:** 50
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def fake_run(cmd, *args, **kwargs):`

### Style: Import sections not in correct order (stdlib, third-party, local)
**File:** `tests/unit/legacy/test_cli_help.py`
**Line:** 2
**Suggestion:** Reorder imports: standard library, third-party, then local imports

### Documentation: Public function missing docstring
**File:** `tests/unit/legacy/test_cli_help.py`
**Line:** 10
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def test_cli_help_no_ansi(monkeypatch, dummy_storage):`

### Documentation: Public function missing docstring
**File:** `tests/unit/legacy/test_cli_help.py`
**Line:** 31
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def test_search_help_includes_interactive(monkeypatch, dummy_storage):`

### Documentation: Public function missing docstring
**File:** `tests/unit/legacy/test_cli_help.py`
**Line:** 49
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def test_search_help_includes_visualize(monkeypatch, dummy_storage):`

### Documentation: Public function missing docstring
**File:** `tests/unit/legacy/test_cli_help.py`
**Line:** 85
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def test_search_help_includes_ontology_flags(monkeypatch, dummy_storage):`

### Documentation: Public function missing docstring
**File:** `tests/unit/legacy/test_cli_help.py`
**Line:** 102
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def test_visualize_help_includes_layout(monkeypatch, dummy_storage):`

### Documentation: Public function missing docstring
**File:** `tests/unit/legacy/test_cli_visualize.py`
**Line:** 17
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def test_render_metrics_panel_bare_mode(monkeypatch):`

### Documentation: Public function missing docstring
**File:** `tests/unit/legacy/test_cli_visualize.py`
**Line:** 30
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def test_summary_table_render():`

### Style: Import sections not in correct order (stdlib, third-party, local)
**File:** `tests/unit/legacy/test_core_modules_additional.py`
**Line:** 3
**Suggestion:** Reorder imports: standard library, third-party, then local imports

### Documentation: Public function missing docstring
**File:** `tests/unit/legacy/test_core_modules_additional.py`
**Line:** 85
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def set_phase(label: str) -> None:`

### Documentation: Public class missing docstring
**File:** `tests/unit/legacy/test_core_modules_additional.py`
**Line:** 269
**Suggestion:** Add a comprehensive docstring explaining purpose and key methods
**Code:** `class TrackingHybrid:`

### Documentation: Public function missing docstring
**File:** `tests/unit/legacy/test_core_modules_additional.py`
**Line:** 278
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def call(*args, **kwargs):`

### Documentation: Public function missing docstring
**File:** `tests/unit/legacy/test_core_modules_additional.py`
**Line:** 309
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def install_backend(docs):`

### Documentation: Public function missing docstring
**File:** `tests/unit/legacy/test_core_modules_additional.py`
**Line:** 322
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def set_storage_results(payload):`

### Documentation: Public function missing docstring
**File:** `tests/unit/legacy/test_core_modules_additional.py`
**Line:** 357
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def test_orchestrator_parse_config_basic():`

### Documentation: Public function missing docstring
**File:** `tests/unit/legacy/test_core_modules_additional.py`
**Line:** 571
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def test_search_stub_backend_return_handles_fallback(_stubbed_search_environment):`

### Documentation: Public function missing docstring
**File:** `tests/unit/legacy/test_core_modules_additional.py`
**Line:** 627
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def test_search_stub_duckduckgo_canonical_query(monkeypatch):`

### Documentation: Public function missing docstring
**File:** `tests/unit/legacy/test_core_modules_additional.py`
**Line:** 665
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def test_search_stub_local_file_canonical_query(monkeypatch, tmp_path):`

### Documentation: Public function missing docstring
**File:** `tests/unit/legacy/test_core_modules_additional.py`
**Line:** 702
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def test_planner_execute(monkeypatch):`

### Documentation: Public class missing docstring
**File:** `tests/unit/legacy/test_core_modules_additional.py`
**Line:** 707
**Suggestion:** Add a comprehensive docstring explaining purpose and key methods
**Code:** `class DummyAdapter:`

### Documentation: Public function missing docstring
**File:** `tests/unit/legacy/test_core_modules_additional.py`
**Line:** 708
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def generate(self, prompt: str, model: str | None = None) -> str:  # noqa: D401`

### Documentation: Public function missing docstring
**File:** `tests/unit/legacy/test_core_modules_additional.py`
**Line:** 721
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def test_storage_setup_teardown(monkeypatch):`

### Documentation: Public class missing docstring
**File:** `tests/unit/legacy/test_core_modules_additional.py`
**Line:** 729
**Suggestion:** Add a comprehensive docstring explaining purpose and key methods
**Code:** `class FakeDuck:`

### Documentation: Public function missing docstring
**File:** `tests/unit/legacy/test_core_modules_additional.py`
**Line:** 733
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def setup(self, path):`

### Documentation: Public function missing docstring
**File:** `tests/unit/legacy/test_core_modules_additional.py`
**Line:** 736
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def get_connection(self):`

### Documentation: Public class missing docstring
**File:** `tests/unit/legacy/test_core_modules_additional.py`
**Line:** 739
**Suggestion:** Add a comprehensive docstring explaining purpose and key methods
**Code:** `class FakeGraph:`

### Documentation: Public function missing docstring
**File:** `tests/unit/legacy/test_core_modules_additional.py`
**Line:** 743
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def open(self, *a, **k):`

### Documentation: Public function missing docstring
**File:** `tests/unit/legacy/test_core_modules_additional.py`
**Line:** 773
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def test_storage_setup_without_kuzu(monkeypatch):`

### Documentation: Public class missing docstring
**File:** `tests/unit/legacy/test_core_modules_additional.py`
**Line:** 776
**Suggestion:** Add a comprehensive docstring explaining purpose and key methods
**Code:** `class FakeDuck:`

### Documentation: Public function missing docstring
**File:** `tests/unit/legacy/test_core_modules_additional.py`
**Line:** 780
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def setup(self, path):  # noqa: D401 - trivial`

### Documentation: Public function missing docstring
**File:** `tests/unit/legacy/test_core_modules_additional.py`
**Line:** 783
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def get_connection(self):  # noqa: D401 - trivial`

### Documentation: Public class missing docstring
**File:** `tests/unit/legacy/test_core_modules_additional.py`
**Line:** 786
**Suggestion:** Add a comprehensive docstring explaining purpose and key methods
**Code:** `class FakeGraph:`

### Documentation: Public function missing docstring
**File:** `tests/unit/legacy/test_core_modules_additional.py`
**Line:** 790
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def open(self, *a, **k):  # noqa: D401 - test stub`

### Documentation: Public function missing docstring
**File:** `tests/unit/legacy/test_duckdb_storage_backend.py`
**Line:** 350
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def side_effect(query, *args, **kwargs):`

### Documentation: Public function missing docstring
**File:** `tests/unit/legacy/test_local_git_backend.py`
**Line:** 21
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def test_local_git_backend_searches_repo(tmp_path, monkeypatch):`

### Documentation: Public function missing docstring
**File:** `tests/unit/legacy/test_local_git_backend.py`
**Line:** 38
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def dummy_connection():`

### Documentation: Public class missing docstring
**File:** `tests/unit/legacy/test_local_git_backend.py`
**Line:** 39
**Suggestion:** Add a comprehensive docstring explaining purpose and key methods
**Code:** `class DummyConn:`

### Documentation: Public function missing docstring
**File:** `tests/unit/legacy/test_local_git_backend.py`
**Line:** 40
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def execute(self, *args, **kwargs):`

### Documentation: Public class missing docstring
**File:** `tests/unit/legacy/test_local_git_backend.py`
**Line:** 41
**Suggestion:** Add a comprehensive docstring explaining purpose and key methods
**Code:** `class Cur:`

### Documentation: Public function missing docstring
**File:** `tests/unit/legacy/test_local_git_backend.py`
**Line:** 42
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def fetchall(self_inner):`

### Style: Import sections not in correct order (stdlib, third-party, local)
**File:** `tests/unit/legacy/test_main_cli.py`
**Line:** 2
**Suggestion:** Reorder imports: standard library, third-party, then local imports

### Documentation: Public function missing docstring
**File:** `tests/unit/legacy/test_main_cli.py`
**Line:** 27
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def test_search_default_output_tty(monkeypatch, mock_run_query, orchestrator):`

### Documentation: Public function missing docstring
**File:** `tests/unit/legacy/test_main_cli.py`
**Line:** 38
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def test_search_default_output_json(monkeypatch, mock_run_query, orchestrator):`

### Documentation: Public function missing docstring
**File:** `tests/unit/legacy/test_main_cli.py`
**Line:** 76
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def test_config_command(monkeypatch, config_loader):`

### Documentation: Public function missing docstring
**File:** `tests/unit/legacy/test_monitor_cli.py`
**Line:** 34
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def dummy_run_query(`

### Documentation: Public function missing docstring
**File:** `tests/unit/legacy/test_monitor_cli.py`
**Line:** 57
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def test_monitor_prompts_and_passes_callbacks(monkeypatch):`

### Documentation: Public function missing docstring
**File:** `tests/unit/legacy/test_monitor_cli.py`
**Line:** 77
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def test_monitor_metrics(monkeypatch):`

### Documentation: Public class missing docstring
**File:** `tests/unit/legacy/test_monitor_cli.py`
**Line:** 86
**Suggestion:** Add a comprehensive docstring explaining purpose and key methods
**Code:** `class Mem:`

### Documentation: Public class missing docstring
**File:** `tests/unit/legacy/test_monitor_cli.py`
**Line:** 90
**Suggestion:** Add a comprehensive docstring explaining purpose and key methods
**Code:** `class Proc:`

### Documentation: Public function missing docstring
**File:** `tests/unit/legacy/test_monitor_cli.py`
**Line:** 91
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def memory_info(self):`

### Documentation: Public function missing docstring
**File:** `tests/unit/legacy/test_monitor_cli.py`
**Line:** 115
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def test_monitor_metrics_default_counters(monkeypatch):`

### Documentation: Public class missing docstring
**File:** `tests/unit/legacy/test_monitor_cli.py`
**Line:** 121
**Suggestion:** Add a comprehensive docstring explaining purpose and key methods
**Code:** `class Mem:`

### Documentation: Public class missing docstring
**File:** `tests/unit/legacy/test_monitor_cli.py`
**Line:** 125
**Suggestion:** Add a comprehensive docstring explaining purpose and key methods
**Code:** `class Proc:`

### Documentation: Public function missing docstring
**File:** `tests/unit/legacy/test_monitor_cli.py`
**Line:** 126
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def memory_info(self):`

### Documentation: Public function missing docstring
**File:** `tests/unit/legacy/test_monitor_cli.py`
**Line:** 144
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def test_metrics_skips_storage(monkeypatch):`

### Documentation: Public function missing docstring
**File:** `tests/unit/legacy/test_monitor_cli.py`
**Line:** 154
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def fake_get_graph():`

### Documentation: Public function missing docstring
**File:** `tests/unit/legacy/test_monitor_cli.py`
**Line:** 165
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def test_storage_teardown_handles_missing_config(monkeypatch):`

### Documentation: Public function missing docstring
**File:** `tests/unit/legacy/test_property_vector_search.py`
**Line:** 16
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def test_vector_search_calls_backend(monkeypatch, query_embedding, k):`

### Documentation: Public function missing docstring
**File:** `tests/unit/legacy/test_property_vector_search.py`
**Line:** 54
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def test_vector_search_invalid(monkeypatch, query_embedding, k):`

### Documentation: Public function missing docstring
**File:** `tests/unit/legacy/test_property_vector_search.py`
**Line:** 81
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def test_vector_search_malformed_embedding(monkeypatch, query_embedding, k):`

### Documentation: Public function missing docstring
**File:** `tests/unit/legacy/test_rdf_update.py`
**Line:** 15
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def test_update_rdf_claim_replace():`

### Documentation: Public function missing docstring
**File:** `tests/unit/legacy/test_rdf_update.py`
**Line:** 43
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def test_update_rdf_claim_partial():`

### Documentation: Public function missing docstring
**File:** `tests/unit/monitor/test_cli_layouts.py`
**Line:** 28
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def test_render_metrics_panel_rich_mode(restore_console: None) -> None:`

### Documentation: Public function missing docstring
**File:** `tests/unit/monitor/test_cli_layouts.py`
**Line:** 34
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def test_visualize_metrics_cli_rich_output(restore_console: None) -> None:`

### Documentation: Public function missing docstring
**File:** `tests/unit/monitor/test_cli_layouts.py`
**Line:** 43
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def test_visualize_metrics_cli_bare_mode(`

### Documentation: Public function missing docstring
**File:** `tests/unit/storage/test_namespace_routing.py`
**Line:** 22
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def test_resolve_namespace_prefers_project_token() -> None:`

### Documentation: Public function missing docstring
**File:** `tests/unit/storage/test_namespace_routing.py`
**Line:** 28
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def test_resolve_namespace_falls_back_to_workspace() -> None:`

### Documentation: Public function missing docstring
**File:** `tests/unit/storage/test_namespace_routing.py`
**Line:** 34
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def test_validate_namespace_routes_detects_cycle() -> None:`

### Documentation: Public function missing docstring
**File:** `tests/unit/storage/test_namespace_routing.py`
**Line:** 39
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def test_search_initialises_namespace_from_tokens(monkeypatch: pytest.MonkeyPatch) -> None:`

### Documentation: Public function missing docstring
**File:** `tests/unit/storage/test_namespace_routing.py`
**Line:** 54
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def test_scholarly_service_search_respects_namespace(monkeypatch: pytest.MonkeyPatch) -> None:`

### Documentation: Public class missing docstring
**File:** `tests/unit/storage/test_namespace_routing.py`
**Line:** 55
**Suggestion:** Add a comprehensive docstring explaining purpose and key methods
**Code:** `class StubFetcher(ScholarlyFetcher):`

### Documentation: Public function missing docstring
**File:** `tests/unit/storage/test_namespace_routing.py`
**Line:** 61
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def search(`

### Documentation: Public function missing docstring
**File:** `tests/unit/storage/test_namespace_routing.py`
**Line:** 73
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def fetch(self, identifier: str) -> PaperDocument:`

### Documentation: Public function missing docstring
**File:** `tests/unit/storage/test_namespace_routing.py`
**Line:** 86
**Suggestion:** Add a comprehensive docstring explaining purpose, parameters, and return value
**Code:** `def test_scholarly_cache_handles_namespace_tokens(`


## Low Issues
### Style: Line exceeds maximum length of 100 characters
**File:** `src/autoresearch/agents/dialectical/fact_checker.py`
**Line:** 196
**Suggestion:** Break long lines or use line continuation
**Code:** `resource_id for resource_id in sorted(targeted_resource_ids) if resource_id not in used_resource_ids`

### Style: Line exceeds maximum length of 100 characters
**File:** `src/autoresearch/main/app.py`
**Line:** 561
**Suggestion:** Break long lines or use line continuation
**Code:** `manifest_id: Optional[str] = typer.Option(None, "--manifest-id", help="Specific manifest identifier."),`

### Style: Line exceeds maximum length of 100 characters
**File:** `src/autoresearch/main/app.py`
**Line:** 567
**Suggestion:** Break long lines or use line continuation
**Code:** `manifest = StorageManager.get_workspace_manifest(workspace, version=version, manifest_id=manifest_id)`

### Style: Line exceeds maximum length of 100 characters
**File:** `src/autoresearch/main/app.py`
**Line:** 579
**Suggestion:** Break long lines or use line continuation
**Code:** `manifest_id: Optional[str] = typer.Option(None, "--manifest-id", help="Manifest identifier override."),`

### Style: Line exceeds maximum length of 100 characters
**File:** `src/autoresearch/main/app.py`
**Line:** 1211
**Suggestion:** Break long lines or use line continuation
**Code:** `"Bare mode disables the dashboard to preserve plain output; using legacy renderer."`

### Style: Line exceeds maximum length of 100 characters
**File:** `src/autoresearch/main/app.py`
**Line:** 1215
**Suggestion:** Break long lines or use line continuation
**Code:** `"Interactive refinement is not supported inside the Textual dashboard; using standard output."`

### Style: Line exceeds maximum length of 100 characters
**File:** `src/autoresearch/main/config_cli.py`
**Line:** 43
**Suggestion:** Break long lines or use line continuation
**Code:** `f"Unknown namespace scope '{scope_key}'. Valid scopes: session, workspace, org, project.",`

### Style: Line exceeds maximum length of 100 characters
**File:** `src/autoresearch/main/config_cli.py`
**Line:** 48
**Suggestion:** Break long lines or use line continuation
**Code:** `f"Invalid route target '{target_key}'. Use session, workspace, org, project, or self.",`

### Style: Line exceeds maximum length of 100 characters
**File:** `src/autoresearch/main/config_cli.py`
**Line:** 116
**Suggestion:** Break long lines or use line continuation
**Code:** `default_namespace = (default or namespaces_cfg.default_namespace or DEFAULT_NAMESPACE_LABEL).strip()`

### Style: Line exceeds maximum length of 100 characters
**File:** `src/autoresearch/orchestration/execution.py`
**Line:** 157
**Suggestion:** Break long lines or use line continuation
**Code:** `f"Agent {agent_name} completed turn (loop {loop + 1}, cycle {state.cycle}) in {duration:.2f}s",`

### Style: Line exceeds maximum length of 100 characters
**File:** `src/autoresearch/orchestration/metrics.py`
**Line:** 236
**Suggestion:** Break long lines or use line continuation
**Code:** `ERROR_COUNTER = _safe_counter("autoresearch_errors_total", "Total number of errors during processing")`

### Style: Line exceeds maximum length of 100 characters
**File:** `src/autoresearch/orchestration/workspace.py`
**Line:** 248
**Suggestion:** Break long lines or use line continuation
**Code:** `include_globs = self._normalise_sequence(metadata.get("file_globs") or metadata.get("include"))`

### Style: Line exceeds maximum length of 100 characters
**File:** `src/autoresearch/orchestration/workspace.py`
**Line:** 253
**Suggestion:** Break long lines or use line continuation
**Code:** `namespaces = self._normalise_sequence(metadata.get("namespaces") or metadata.get("namespace"))`

### Style: Line exceeds maximum length of 100 characters
**File:** `src/autoresearch/orchestration/workspace.py`
**Line:** 328
**Suggestion:** Break long lines or use line continuation
**Code:** `reference_map = {resource.reference: resource.resource_id for resource in manifest.resources}`

### Style: Line exceeds maximum length of 100 characters
**File:** `src/autoresearch/resources/scholarly/fetchers.py`
**Line:** 134
**Suggestion:** Break long lines or use line continuation
**Code:** `identifier_value = str(payload.get("paperId") or payload.get("id") or payload.get("slug") or "")`

### Style: Line exceeds maximum length of 100 characters
**File:** `src/autoresearch/resources/scholarly/fetchers.py`
**Line:** 150
**Suggestion:** Break long lines or use line continuation
**Code:** `published = _parse_timestamp(str(payload.get("publishedAt") or payload.get("published") or ""))`

### Style: Line exceeds maximum length of 100 characters
**File:** `src/autoresearch/search/core.py`
**Line:** 988
**Suggestion:** Break long lines or use line continuation
**Code:** `repo_specs = search_section.get("repositories") if isinstance(search_section, Mapping) else None`

### Style: Line exceeds maximum length of 100 characters
**File:** `src/autoresearch/search/core.py`
**Line:** 2322
**Suggestion:** Break long lines or use line continuation
**Code:** `namespace_label = str(hit.get("namespace") or namespace or DEFAULT_NAMESPACE_LABEL)`

### Style: Line exceeds maximum length of 100 characters
**File:** `src/autoresearch/search/core.py`
**Line:** 2636
**Suggestion:** Break long lines or use line continuation
**Code:** `active_hints = workspace_hints if workspace_hints is not None else get_active_workspace_hints()`

### Style: Line exceeds maximum length of 100 characters
**File:** `src/autoresearch/search/core.py`
**Line:** 2975
**Suggestion:** Break long lines or use line continuation
**Code:** `suggestion="Check your network connection and ensure the search backend is properly configured",`

### Style: Line exceeds maximum length of 100 characters
**File:** `src/autoresearch/search/core.py`
**Line:** 3849
**Suggestion:** Break long lines or use line continuation
**Code:** `normalised = _normalise_resource_specs(cast(Sequence[Mapping[str, Any]] | None, resource_specs))`

### Style: Line exceeds maximum length of 100 characters
**File:** `src/autoresearch/search/core.py`
**Line:** 4079
**Suggestion:** Break long lines or use line continuation
**Code:** `"commit_hash VARCHAR PRIMARY KEY, author VARCHAR, date TIMESTAMP, message VARCHAR, diff VARCHAR)"`

### Style: Line exceeds maximum length of 100 characters
**File:** `src/autoresearch/search/core.py`
**Line:** 4111
**Suggestion:** Break long lines or use line continuation
**Code:** `snippet = snippet_match.group(0).strip() if snippet_match else part[:200]`

### Style: Line exceeds maximum length of 100 characters
**File:** `src/autoresearch/search/core.py`
**Line:** 4156
**Suggestion:** Break long lines or use line continuation
**Code:** `if lower_query in getattr(commit, "message", "").lower() and len(results) < max_results:`

### Style: Line exceeds maximum length of 100 characters
**File:** `src/autoresearch/storage.py`
**Line:** 653
**Suggestion:** Break long lines or use line continuation
**Code:** `resources = [WorkspaceResource.from_payload(cast(JSONMapping, item)) for item in resources_raw]`

### Style: Line exceeds maximum length of 100 characters
**File:** `src/autoresearch/storage.py`
**Line:** 1098
**Suggestion:** Break long lines or use line continuation
**Code:** `If a custom implementation is set via set_delegate(), the call is delegated to that implementation.`

### Style: Line exceeds maximum length of 100 characters
**File:** `src/autoresearch/storage.py`
**Line:** 1197
**Suggestion:** Break long lines or use line continuation
**Code:** `payload = manifest.to_payload() if isinstance(manifest, WorkspaceManifest) else to_json_dict(manifest)`

### Style: Line exceeds maximum length of 100 characters
**File:** `src/autoresearch/storage.py`
**Line:** 1212
**Suggestion:** Break long lines or use line continuation
**Code:** `return _delegate.get_workspace_manifest(workspace_id, version=version, manifest_id=manifest_id)`

### Style: Line exceeds maximum length of 100 characters
**File:** `src/autoresearch/storage.py`
**Line:** 1366
**Suggestion:** Break long lines or use line continuation
**Code:** `str | None: The ID of the node with the lowest confidence score, or None if the graph is empty.`

### Style: Line exceeds maximum length of 100 characters
**File:** `src/autoresearch/storage.py`
**Line:** 1369
**Suggestion:** Break long lines or use line continuation
**Code:** `This method only identifies the node for eviction and removes it from the LRU cache if present.`

### Style: Line exceeds maximum length of 100 characters
**File:** `src/autoresearch/storage.py`
**Line:** 1842
**Suggestion:** Break long lines or use line continuation
**Code:** `claim: The claim to validate as a dictionary. Must contain 'id', 'type', and 'content' fields.`

### Style: Line exceeds maximum length of 100 characters
**File:** `src/autoresearch/storage.py`
**Line:** 1899
**Suggestion:** Break long lines or use line continuation
**Code:** `suggestion="Initialize the storage system by calling StorageManager.setup() before performing operations",`

### Style: Line exceeds maximum length of 100 characters
**File:** `src/autoresearch/storage.py`
**Line:** 1904
**Suggestion:** Break long lines or use line continuation
**Code:** `suggestion="Initialize the storage system by calling StorageManager.setup() before performing operations",`

### Style: Line exceeds maximum length of 100 characters
**File:** `src/autoresearch/storage.py`
**Line:** 1909
**Suggestion:** Break long lines or use line continuation
**Code:** `suggestion="Initialize the storage system by calling StorageManager.setup() before performing operations",`

### Style: Line exceeds maximum length of 100 characters
**File:** `src/autoresearch/storage.py`
**Line:** 2035
**Suggestion:** Break long lines or use line continuation
**Code:** `next_version = StorageManager.context.db_backend.next_workspace_manifest_version(workspace_id)`

### Style: Line exceeds maximum length of 100 characters
**File:** `src/autoresearch/storage.py`
**Line:** 2375
**Suggestion:** Break long lines or use line continuation
**Code:** `namespaces = provenance.get(claim_id) or {entry.get("namespace", DEFAULT_NAMESPACE_LABEL)}`

### Style: Line exceeds maximum length of 100 characters
**File:** `src/autoresearch/storage.py`
**Line:** 2887
**Suggestion:** Break long lines or use line continuation
**Code:** `suggestion="Check that the VSS extension is properly installed and that embeddings exist in the database",`

### Style: Line exceeds maximum length of 100 characters
**File:** `src/autoresearch/storage.py`
**Line:** 3042
**Suggestion:** Break long lines or use line continuation
**Code:** `NotFoundError: If the connection cannot be initialized or remains None after initialization.`

### Style: Line exceeds maximum length of 100 characters
**File:** `src/autoresearch/storage.py`
**Line:** 3088
**Suggestion:** Break long lines or use line continuation
**Code:** `NotFoundError: If the RDF store cannot be initialized or remains None after initialization.`

### Style: Line exceeds maximum length of 100 characters
**File:** `src/autoresearch/storage_backends.py`
**Line:** 327
**Suggestion:** Break long lines or use line continuation
**Code:** `"sample_size INTEGER, sources VARCHAR, notes VARCHAR, provenance VARCHAR, created_at TIMESTAMP)"`

### Style: Line exceeds maximum length of 100 characters
**File:** `src/autoresearch/storage_backends.py`
**Line:** 573
**Suggestion:** Break long lines or use line continuation
**Code:** `"sample_size INTEGER, sources VARCHAR, notes VARCHAR, provenance VARCHAR, created_at TIMESTAMP)"`

### Style: Line exceeds maximum length of 100 characters
**File:** `src/autoresearch/storage_backends.py`
**Line:** 665
**Suggestion:** Break long lines or use line continuation
**Code:** `f"Failed to enable experimental HNSW persistence: {e}. This is expected if using an older VSS extension version."`

### Style: Line exceeds maximum length of 100 characters
**File:** `src/autoresearch/storage_backends.py`
**Line:** 682
**Suggestion:** Break long lines or use line continuation
**Code:** `# If the table is empty, insert a dummy embedding to ensure the HNSW index can be created`

### Style: Line exceeds maximum length of 100 characters
**File:** `src/autoresearch/storage_backends.py`
**Line:** 852
**Suggestion:** Break long lines or use line continuation
**Code:** `f"INSERT INTO {tables.kg_entities} VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)",`

### Style: Line exceeds maximum length of 100 characters
**File:** `src/autoresearch/storage_backends.py`
**Line:** 896
**Suggestion:** Break long lines or use line continuation
**Code:** `f"INSERT INTO {tables.kg_relations} VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)",`

### Style: Line exceeds maximum length of 100 characters
**File:** `src/autoresearch/storage_backends.py`
**Line:** 1066
**Suggestion:** Break long lines or use line continuation
**Code:** `"(audit_id, claim_id, status, entailment, variance, instability, sample_size, "`

### Style: Line exceeds maximum length of 100 characters
**File:** `src/autoresearch/storage_backends.py`
**Line:** 1067
**Suggestion:** Break long lines or use line continuation
**Code:** `"sources, notes, provenance, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"`

### Style: Line exceeds maximum length of 100 characters
**File:** `src/autoresearch/storage_backends.py`
**Line:** 1207
**Suggestion:** Break long lines or use line continuation
**Code:** `"(workspace_id, manifest_id, version, name, parent_manifest_id, created_at, resources, annotations) "`

### Style: Line exceeds maximum length of 100 characters
**File:** `src/autoresearch/storage_backends.py`
**Line:** 1231
**Suggestion:** Break long lines or use line continuation
**Code:** `"SELECT workspace_id, manifest_id, version, name, parent_manifest_id, created_at, resources, annotations "`

### Style: Line exceeds maximum length of 100 characters
**File:** `src/autoresearch/storage_backends.py`
**Line:** 1293
**Suggestion:** Break long lines or use line continuation
**Code:** `if not isinstance(embedding_payload, Sequence) or isinstance(embedding_payload, (str, bytes)):`

### Style: Line exceeds maximum length of 100 characters
**File:** `src/autoresearch/storage_backends.py`
**Line:** 1299
**Suggestion:** Break long lines or use line continuation
**Code:** `"(provider, paper_id, metadata, provenance, cache_path, references_json, embedding) "`

### Style: Line exceeds maximum length of 100 characters
**File:** `src/autoresearch/storage_backends.py`
**Line:** 1302
**Suggestion:** Break long lines or use line continuation
**Code:** `"metadata=excluded.metadata, provenance=excluded.provenance, cache_path=excluded.cache_path, "`

### Style: Line exceeds maximum length of 100 characters
**File:** `src/autoresearch/storage_backends.py`
**Line:** 1328
**Suggestion:** Break long lines or use line continuation
**Code:** `f"SELECT provider, paper_id, metadata, provenance, cache_path, references_json, embedding "`

### Style: Line exceeds maximum length of 100 characters
**File:** `src/autoresearch/storage_backends.py`
**Line:** 1364
**Suggestion:** Break long lines or use line continuation
**Code:** `f"SELECT provider, paper_id, metadata, provenance, cache_path, references_json, embedding "`

### Style: Line exceeds maximum length of 100 characters
**File:** `src/autoresearch/storage_backends.py`
**Line:** 1401
**Suggestion:** Break long lines or use line continuation
**Code:** `"SELECT workspace_id, manifest_id, version, name, parent_manifest_id, created_at, resources, annotations "`

### Style: Line exceeds maximum length of 100 characters
**File:** `src/autoresearch/storage_backends.py`
**Line:** 1456
**Suggestion:** Break long lines or use line continuation
**Code:** `"SELECT COALESCE(MAX(version), 0) FROM workspace_manifests WHERE workspace_id=?",`

### Style: Line exceeds maximum length of 100 characters
**File:** `src/autoresearch/storage_backends.py`
**Line:** 1535
**Suggestion:** Break long lines or use line continuation
**Code:** `suggestion="Ensure the VSS extension is properly installed and enabled in the configuration",`

### Style: Line exceeds maximum length of 100 characters
**File:** `src/autoresearch/storage_backends.py`
**Line:** 1605
**Suggestion:** Break long lines or use line continuation
**Code:** `WHEN '{cfg.storage.hnsw_metric if hasattr(cfg, "storage") and hasattr(cfg.storage, "hnsw_metric") else "cosine"}' = 'cosine' THEN 1 - (e.embedding <-> {vector_literal})`

### Style: Line exceeds maximum length of 100 characters
**File:** `src/autoresearch/storage_backends.py`
**Line:** 1606
**Suggestion:** Break long lines or use line continuation
**Code:** `WHEN '{cfg.storage.hnsw_metric if hasattr(cfg, "storage") and hasattr(cfg.storage, "hnsw_metric") else "cosine"}' = 'ip' THEN 1 - (e.embedding <=> {vector_literal})`

### Style: Line exceeds maximum length of 100 characters
**File:** `src/autoresearch/storage_backends.py`
**Line:** 1645
**Suggestion:** Break long lines or use line continuation
**Code:** `WHEN '{cfg.storage.hnsw_metric if hasattr(cfg, "storage") and hasattr(cfg.storage, "hnsw_metric") else "cosine"}' = 'cosine' THEN 1 - (embedding <-> {vector_literal})`

### Style: Line exceeds maximum length of 100 characters
**File:** `src/autoresearch/storage_backends.py`
**Line:** 1646
**Suggestion:** Break long lines or use line continuation
**Code:** `WHEN '{cfg.storage.hnsw_metric if hasattr(cfg, "storage") and hasattr(cfg.storage, "hnsw_metric") else "cosine"}' = 'ip' THEN 1 - (embedding <=> {vector_literal})`

### Style: Line exceeds maximum length of 100 characters
**File:** `src/autoresearch/storage_backends.py`
**Line:** 1708
**Suggestion:** Break long lines or use line continuation
**Code:** `suggestion="Check that the VSS extension is properly installed and that embeddings exist in the database",`

### Style: Line exceeds maximum length of 100 characters
**File:** `src/autoresearch/storage_backends.py`
**Line:** 1825
**Suggestion:** Break long lines or use line continuation
**Code:** `"CREATE NODE TABLE IF NOT EXISTS Claim(id STRING PRIMARY KEY, content STRING, conf DOUBLE)"`

### Style: Line exceeds maximum length of 100 characters
**File:** `src/autoresearch/ui/desktop/knowledge_graph_view.py`
**Line:** 157
**Suggestion:** Break long lines or use line continuation
**Code:** `def _normalise_graph_data(self, graph_data: Mapping[str, Any] | Any | None) -> Mapping[str, Any] | None:`

### Style: Line exceeds maximum length of 100 characters
**File:** `src/autoresearch/ui/desktop/knowledge_graph_view.py`
**Line:** 161
**Suggestion:** Break long lines or use line continuation
**Code:** `if nx and isinstance(graph_data, nx.Graph):  # pragma: no branch - depends on optional import`

### Style: Line exceeds maximum length of 100 characters
**File:** `src/autoresearch/ui/desktop/knowledge_graph_view.py`
**Line:** 187
**Suggestion:** Break long lines or use line continuation
**Code:** `edges: Sequence[Sequence[Any]] = self._graph_data.get("edges", [])  # type: ignore[assignment]`

### Style: Line exceeds maximum length of 100 characters
**File:** `src/autoresearch/ui/desktop/main_window.py`
**Line:** 584
**Suggestion:** Break long lines or use line continuation
**Code:** `initial_prompt = self.query_panel.query_input.toPlainText()  # type: ignore[attr-defined]`

### Style: Line exceeds maximum length of 100 characters
**File:** `src/autoresearch/ui/desktop/main_window.py`
**Line:** 717
**Suggestion:** Break long lines or use line continuation
**Code:** `default_namespace, _, _ = StorageManager._namespace_settings() if StorageManager else ("__default__", {}, {})`

### Style: Line exceeds maximum length of 100 characters
**File:** `src/autoresearch/ui/desktop/main_window.py`
**Line:** 759
**Suggestion:** Break long lines or use line continuation
**Code:** `f"{item.metadata.title} ({item.metadata.identifier.provider}:{item.metadata.primary_key()})"`

### Style: Line exceeds maximum length of 100 characters
**File:** `src/autoresearch/ui/desktop/main_window.py`
**Line:** 790
**Suggestion:** Break long lines or use line continuation
**Code:** `"reference": f"{cached.metadata.identifier.provider}:{cached.metadata.primary_key()}",`

### Style: Line exceeds maximum length of 100 characters
**File:** `src/autoresearch/ui/desktop/results_table.py`
**Line:** 41
**Suggestion:** Break long lines or use line continuation
**Code:** `def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: D401 - Qt signature  # type: ignore[override]`

### Style: Line exceeds maximum length of 100 characters
**File:** `src/autoresearch/ui/desktop/results_table.py`
**Line:** 46
**Suggestion:** Break long lines or use line continuation
**Code:** `def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: D401 - Qt signature  # type: ignore[override]`

### Style: Line exceeds maximum length of 100 characters
**File:** `src/autoresearch/ui/desktop/results_table.py`
**Line:** 51
**Suggestion:** Break long lines or use line continuation
**Code:** `def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:  # noqa: D401 - Qt signature  # type: ignore[override]`

### Style: Line exceeds maximum length of 100 characters
**File:** `src/autoresearch/ui/desktop/results_table.py`
**Line:** 80
**Suggestion:** Break long lines or use line continuation
**Code:** `if orientation == Qt.Horizontal and 0 <= section < len(self._HEADERS):  # type: ignore[attr-defined]`

### Style: Line exceeds maximum length of 100 characters
**File:** `src/autoresearch/ui/desktop/results_table.py`
**Line:** 83
**Suggestion:** Break long lines or use line continuation
**Code:** `if orientation == Qt.Vertical and 0 <= section < len(self._rows):  # type: ignore[attr-defined]`

### Style: Line exceeds maximum length of 100 characters
**File:** `src/autoresearch/ui/desktop/results_table.py`
**Line:** 88
**Suggestion:** Break long lines or use line continuation
**Code:** `def flags(self, index: QModelIndex) -> Qt.ItemFlags:  # noqa: D401 - Qt signature  # type: ignore[override]`

### Style: Line exceeds maximum length of 100 characters
**File:** `src/autoresearch/ui/desktop/results_table.py`
**Line:** 156
**Suggestion:** Break long lines or use line continuation
**Code:** `def setModel(self, model: QAbstractTableModel) -> None:  # noqa: N802 - Qt override  # type: ignore[override]`

### Style: Line exceeds maximum length of 100 characters
**File:** `tests/behavior/steps/dkg_persistence_steps.py`
**Line:** 55
**Suggestion:** Break long lines or use line continuation
**Code:** `suggestion="Initialize the storage system by calling StorageManager.setup() before performing operations",`

### Style: Line exceeds maximum length of 100 characters
**File:** `tests/behavior/steps/dkg_persistence_steps.py`
**Line:** 267
**Suggestion:** Break long lines or use line continuation
**Code:** `"""Attempt to persist a valid claim to uninitialized storage and store any exception raised in the context."""`

### Style: Line exceeds maximum length of 100 characters
**File:** `tests/behavior/steps/dkg_persistence_steps.py`
**Line:** 277
**Suggestion:** Break long lines or use line continuation
**Code:** `# No need to call uninit_storage() as monkeypatch will automatically restore the original methods`

### Style: Line exceeds maximum length of 100 characters
**File:** `tests/behavior/steps/scholarly_steps.py`
**Line:** 30
**Suggestion:** Break long lines or use line continuation
**Code:** `identifier = PaperIdentifier(provider="huggingface", value=title.lower().replace(" ", "-"), namespace=namespace)`

### Style: Line exceeds maximum length of 100 characters
**File:** `tests/ui/desktop/test_desktop_integration.py`
**Line:** 64
**Suggestion:** Break long lines or use line continuation
**Code:** `monkeypatch.setattr(QtCore.QThreadPool, "globalInstance", staticmethod(lambda: _ImmediateThreadPool()))`

### Style: Line exceeds maximum length of 100 characters
**File:** `tests/ui/desktop/test_desktop_integration.py`
**Line:** 66
**Suggestion:** Break long lines or use line continuation
**Code:** `monkeypatch.setattr(main_window_module, "get_orchestration_metrics", lambda: None, raising=False)`

### Style: Line exceeds maximum length of 100 characters
**File:** `tests/ui/desktop/test_desktop_integration.py`
**Line:** 168
**Suggestion:** Break long lines or use line continuation
**Code:** `graph_data = window.results_display.knowledge_graph_view._graph_data  # type: ignore[attr-defined]`

### Style: Line exceeds maximum length of 100 characters
**File:** `tests/ui/desktop/test_results_display.py`
**Line:** 156
**Suggestion:** Break long lines or use line continuation
**Code:** `table_in_tab = answer_tab.findChild(type(display.search_results_view), "results-display-search-table")`

### Style: Line exceeds maximum length of 100 characters
**File:** `tests/unit/legacy/test_cache.py`
**Line:** 490
**Suggestion:** Break long lines or use line continuation
**Code:** `), "If legacy cache entries fail to migrate, why would the backend stay idle on the first hit?"`

### Style: Line exceeds maximum length of 100 characters
**File:** `tests/unit/legacy/test_cache.py`
**Line:** 509
**Suggestion:** Break long lines or use line continuation
**Code:** `), "When migration runs, shouldn't the hashed key inherit the legacy payload for future hits?"`

### Style: Line exceeds maximum length of 100 characters
**File:** `tests/unit/legacy/test_cache.py`
**Line:** 603
**Suggestion:** Break long lines or use line continuation
**Code:** `), "If v2 cache entries failed to migrate, why would the backend fire before leveraging the alias?"`

### Style: Line exceeds maximum length of 100 characters
**File:** `tests/unit/legacy/test_cache.py`
**Line:** 649
**Suggestion:** Break long lines or use line continuation
**Code:** `), "Once accessed via an alias, shouldn't the upgraded cache persist under the new primary hash?"`

### Style: Line exceeds maximum length of 100 characters
**File:** `tests/unit/legacy/test_cache.py`
**Line:** 667
**Suggestion:** Break long lines or use line continuation
**Code:** `), "If alias hits leaked across namespaces, why would the alternate view touch the backend at all?"`

### Style: Line exceeds maximum length of 100 characters
**File:** `tests/unit/legacy/test_cache.py`
**Line:** 848
**Suggestion:** Break long lines or use line continuation
**Code:** `), "If cache fingerprints collide, why would sequential repeats hit the backend again?"`

### Style: Line exceeds maximum length of 100 characters
**File:** `tests/unit/legacy/test_cache.py`
**Line:** 851
**Suggestion:** Break long lines or use line continuation
**Code:** `), "How could identical toggle states yield differing fingerprints and still reuse cache entries?"`

### Style: Line exceeds maximum length of 100 characters
**File:** `tests/unit/legacy/test_cache.py`
**Line:** 855
**Suggestion:** Break long lines or use line continuation
**Code:** `), "When encountering a new toggle combination, shouldn't the backend fetch occur exactly once?"`

### Style: Line exceeds maximum length of 100 characters
**File:** `tests/unit/legacy/test_cache.py`
**Line:** 862
**Suggestion:** Break long lines or use line continuation
**Code:** `), "If namespaces drifted cache slots, why would the alternate view produce different results?"`

### Style: Line exceeds maximum length of 100 characters
**File:** `tests/unit/legacy/test_cache.py`
**Line:** 877
**Suggestion:** Break long lines or use line continuation
**Code:** `), "How would cached namespaces regress if repeated draws still triggered backend calls?"`

### Style: Line exceeds maximum length of 100 characters
**File:** `tests/unit/legacy/test_cache.py`
**Line:** 884
**Suggestion:** Break long lines or use line continuation
**Code:** `), "Why would a fresh namespace skip backend execution for a new toggle combination?"`

### Style: Line exceeds maximum length of 100 characters
**File:** `tests/unit/legacy/test_cache.py`
**Line:** 892
**Suggestion:** Break long lines or use line continuation
**Code:** `), "When namespaces reuse cached payloads, shouldn't backend calls still match unique combinations?"`

### Style: Line exceeds maximum length of 100 characters
**File:** `tests/unit/legacy/test_cache.py`
**Line:** 1003
**Suggestion:** Break long lines or use line continuation
**Code:** `), "If namespace traces failed to capture fingerprints, what evidence would confirm the initial store?"`

### Style: Line exceeds maximum length of 100 characters
**File:** `tests/unit/legacy/test_cache.py`
**Line:** 1125
**Suggestion:** Break long lines or use line continuation
**Code:** `), "If cache traces skipped canonical fingerprints, how could we validate deterministic storage events?"`

### Style: Line exceeds maximum length of 100 characters
**File:** `tests/unit/legacy/test_cache.py`
**Line:** 1129
**Suggestion:** Break long lines or use line continuation
**Code:** `), "When duckdb lookup paths change, shouldn't backend calls align with the expected storage coverage?"`

### Style: Line exceeds maximum length of 100 characters
**File:** `tests/unit/legacy/test_cache.py`
**Line:** 1141
**Suggestion:** Break long lines or use line continuation
**Code:** `), "When duckdb coverage is deterministic, why would repeated lookups trigger additional backend calls?"`

### Style: Line exceeds maximum length of 100 characters
**File:** `tests/unit/legacy/test_cache.py`
**Line:** 1147
**Suggestion:** Break long lines or use line continuation
**Code:** `), "Without stable cache keys, how could sequential storage blends return identical payloads?"`

### Style: Line exceeds maximum length of 100 characters
**File:** `tests/unit/legacy/test_cache.py`
**Line:** 1163
**Suggestion:** Break long lines or use line continuation
**Code:** `), "If cache hits were non-deterministic, how could we reconcile the trace with expected slot usage?"`

### Style: Line exceeds maximum length of 100 characters
**File:** `tests/unit/legacy/test_cache.py`
**Line:** 1198
**Suggestion:** Break long lines or use line continuation
**Code:** `), "If storage hints were not canonicalised, why would shuffled duplicates map to identical cache slots?"`

### Style: Line exceeds maximum length of 100 characters
**File:** `tests/unit/legacy/test_cache.py`
**Line:** 1221
**Suggestion:** Break long lines or use line continuation
**Code:** `), "If interleaved storage altered the fingerprint, what mechanism would keep cache hits deterministic?"`

### Style: Line exceeds maximum length of 100 characters
**File:** `tests/unit/legacy/test_cache.py`
**Line:** 1228
**Suggestion:** Break long lines or use line continuation
**Code:** `), "When cache keys stabilise embeddings, shouldn't vector fetches match the expected backend usage?"`

### Style: Line exceeds maximum length of 100 characters
**File:** `tests/unit/legacy/test_core_modules_additional.py`
**Line:** 251
**Suggestion:** Break long lines or use line continuation
**Code:** `def _stub_storage_lookup(subject, query, query_embedding, backend_results, max_results, *, workspace_hints: Mapping[str, Any] | None = None, workspace_filters: Mapping[str, Any] | None = None):`

### Style: Line exceeds maximum length of 100 characters
**File:** `tests/unit/legacy/test_duckdb_storage_backend.py`
**Line:** 201
**Suggestion:** Break long lines or use line continuation
**Code:** `"CREATE TABLE IF NOT EXISTS nodes(id VARCHAR, type VARCHAR, content VARCHAR, conf DOUBLE, ts TIMESTAMP)"`

### Style: Line exceeds maximum length of 100 characters
**File:** `tests/unit/storage/test_namespace_routing.py`
**Line:** 69
**Suggestion:** Break long lines or use line continuation
**Code:** `identifier = PaperIdentifier(provider=self.provider, value="id", namespace=namespace or "__public__")`

