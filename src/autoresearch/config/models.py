from __future__ import annotations

from typing import Any, ClassVar, Dict, List, Mapping, Optional, Self, cast

from pydantic import BaseModel, Field, ValidationError, field_validator
from pydantic.functional_validators import model_validator
from pydantic_settings import SettingsConfigDict

from ..orchestration.reasoning import ReasoningMode
from .validators import (
    normalize_ranking_weights,
    validate_eviction_policy,
    validate_rdf_backend,
    validate_reasoning_mode,
    validate_token_budget,
)


class ContextAwareSearchConfig(BaseModel):
    """Configuration for context-aware search functionality."""

    enabled: bool = Field(default=True)
    use_query_expansion: bool = Field(default=True)
    expansion_factor: float = Field(default=0.3, ge=0.0, le=1.0)
    use_entity_recognition: bool = Field(default=True)
    entity_weight: float = Field(default=0.5, ge=0.0, le=1.0)
    use_topic_modeling: bool = Field(default=True)
    num_topics: int = Field(default=5, ge=1, le=20)
    topic_weight: float = Field(default=0.3, ge=0.0, le=1.0)
    use_search_history: bool = Field(default=True)
    history_weight: float = Field(default=0.2, ge=0.0, le=1.0)
    max_history_items: int = Field(default=10, ge=1, le=100)
    graph_pipeline_enabled: bool = Field(
        default=True,
        description="Enable knowledge graph construction from retrieval snippets.",
    )
    graph_max_entities: int = Field(
        default=256,
        ge=1,
        description="Maximum number of unique entities captured per ingestion batch.",
    )
    graph_max_edges: int = Field(
        default=512,
        ge=1,
        description="Maximum number of relations extracted per ingestion batch.",
    )
    graph_contradiction_weight: float = Field(
        default=0.35,
        ge=0.0,
        le=1.0,
        description="Weight applied to contradiction signals derived from the graph.",
    )
    graph_signal_weight: float = Field(
        default=0.2,
        ge=0.0,
        le=1.0,
        description="Weight applied to supportive similarity signals derived from the graph.",
    )
    planner_graph_conditioning: bool = Field(
        default=False,
        description=(
            "Inject knowledge graph contradictions, neighbours, and provenance into planner "
            "prompts when true."
        ),
    )


class LocalFileConfig(BaseModel):
    """Configuration for the local_file search backend."""

    path: str = ""
    file_types: List[str] = Field(default_factory=lambda: ["txt"])


class LocalGitConfig(BaseModel):
    """Configuration for the local_git search backend."""

    repo_path: str = ""
    branches: List[str] = Field(default_factory=lambda: ["main"])
    history_depth: int = Field(default=50, ge=1)


class ModelRouteProfile(BaseModel):
    """Describe pricing and latency characteristics for a single model."""

    prompt_cost_per_1k: float = Field(default=0.0, ge=0.0)
    completion_cost_per_1k: float = Field(default=0.0, ge=0.0)
    latency_p95_ms: float = Field(default=1000.0, ge=0.0)
    quality_rank: int = Field(
        default=0,
        description="Relative quality score; higher values are preferred",
    )

    def cost_per_token(self) -> float:
        """Return blended per-token cost for the profile."""

        return (self.prompt_cost_per_1k + self.completion_cost_per_1k) / 1000.0


class RoleRoutingPolicy(BaseModel):
    """Role-specific routing preferences and escalation thresholds."""

    preferred_models: List[str] = Field(
        default_factory=list,
        description="Ordered list of preferred models when budget allows",
    )
    allowed_models: List[str] = Field(
        default_factory=list,
        description="Allowlist restricting eligible models for the role",
    )
    default_model: str | None = Field(
        default=None,
        description="Model applied when no prior selection exists",
    )
    token_budget: int | None = Field(
        default=None,
        ge=0,
        description="Optional absolute token ceiling reserved for the role",
    )
    token_share: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Fraction of the global token budget reserved for the role",
    )
    latency_slo_ms: float | None = Field(
        default=None,
        ge=0.0,
        description="Role-specific latency objective in milliseconds",
    )
    confidence_threshold: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description=(
            "Minimum confidence required to stay on the preferred routing "
            "profile; below this threshold the router escalates"
        ),
    )
    escalation_model: str | None = Field(
        default=None,
        description="Preferred model when escalating due to low confidence",
    )
    escalation_reason: str | None = Field(
        default=None,
        description="Optional human-readable escalation rationale",
    )


class ModelRoutingConfig(BaseModel):
    """Global configuration controlling budget-aware model routing."""

    enabled: bool = Field(
        default=False,
        description="Enable budget-aware routing when true",
    )
    default_latency_slo_ms: float = Field(
        default=5000.0,
        ge=0.0,
        description="Fallback latency SLO applied when agents omit overrides",
    )
    budget_pressure_ratio: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description=(
            "Fraction of an agent's token share that must remain before routing "
            "prefers cheaper models"
        ),
    )
    strategy_name: str = Field(
        default="balanced",
        description="Identifier for the active routing strategy variant",
    )
    role_policies: Dict[str, RoleRoutingPolicy] = Field(
        default_factory=dict,
        description="Mapping of agent roles to routing policies",
    )
    model_profiles: Dict[str, ModelRouteProfile] = Field(
        default_factory=dict,
        description="Cost and latency metadata for eligible models",
    )

    def policy_for(self, agent_name: str) -> tuple[str | None, RoleRoutingPolicy | None]:
        """Return ``(key, policy)`` for ``agent_name`` when configured."""

        if not agent_name:
            return None, None
        lowered = agent_name.lower()
        for key, policy in self.role_policies.items():
            if key.lower() == lowered:
                return key, policy
        wildcard = self.role_policies.get("*")
        if wildcard is not None:
            return "*", wildcard
        return None, None


class SearchConfig(BaseModel):
    """Configuration for search functionality."""

    backends: List[str] = Field(default=["serper"])
    embedding_backends: List[str] = Field(default_factory=list)
    max_results_per_query: int = Field(default=5, ge=1)
    hybrid_query: bool = Field(
        default=False,
        description="Combine keyword and semantic search when true",
    )
    use_semantic_similarity: bool = Field(default=True)
    use_bm25: bool = Field(default=True)
    semantic_similarity_weight: float = Field(default=0.5, ge=0.0)
    bm25_weight: float = Field(default=0.3, ge=0.0)
    source_credibility_weight: float = Field(default=0.2, ge=0.0)
    use_source_credibility: bool = Field(default=True)
    domain_authority_factor: float = Field(default=0.6, ge=0.0, le=1.0)
    citation_count_factor: float = Field(default=0.4, ge=0.0, le=1.0)
    use_feedback: bool = Field(default=False)
    feedback_weight: float = Field(default=0.3, ge=0.0, le=1.0)
    context_aware: ContextAwareSearchConfig = Field(default_factory=ContextAwareSearchConfig)
    local_file: LocalFileConfig = Field(default_factory=LocalFileConfig)
    local_git: LocalGitConfig = Field(default_factory=LocalGitConfig)
    max_workers: int = Field(default=4, ge=1)
    http_pool_size: int = Field(default=10, ge=1)
    shared_cache: bool = Field(
        default=True,
        description="Reuse the process-wide search cache when true",
    )
    cache_namespace: Optional[str] = Field(
        default=None,
        description="Optional namespace isolating cached search results",
    )
    parallel_enabled: bool = Field(
        default=True,
        description="Fan out search backends concurrently when true",
    )
    parallel_prefetch: int = Field(
        default=0,
        ge=0,
        description="Sequential backends executed before launching parallel lookups",
    )

    _normalize_ranking_weights = model_validator(mode="after")(normalize_ranking_weights)


class StorageConfig(BaseModel):
    """Storage configuration for DuckDB, RDF, and more.

    Attributes:
        ontology_reasoner_timeout: Timeout for ontology reasoning in seconds.
            Defaults to ``None`` meaning no timeout.
        ontology_reasoner_max_triples: Skip reasoning when triple count exceeds
            this value. Defaults to ``None`` meaning no limit.
    """

    duckdb_path: str = Field(default="autoresearch.duckdb")
    vector_extension: bool = Field(default=True)
    vector_extension_path: Optional[str] = Field(default=None)
    hnsw_m: int = Field(default=16, ge=4)
    hnsw_ef_construction: int = Field(default=200, ge=32)
    hnsw_metric: str = Field(default="l2sq")
    hnsw_ef_search: int = Field(default=10, ge=1)
    hnsw_auto_tune: bool = Field(default=True)
    vector_nprobe: int = Field(default=10, ge=1)
    vector_search_batch_size: Optional[int] = Field(default=None, ge=1)
    vector_search_timeout_ms: Optional[int] = Field(default=None, ge=1)
    rdf_backend: str = Field(default="memory")
    rdf_path: str = Field(default="rdf_store")
    ontology_reasoner: str = Field(default="owlrl")
    ontology_reasoner_timeout: float | None = Field(
        default=None,
        description="Reasoner timeout in seconds. None disables the timeout.",
    )
    ontology_reasoner_max_triples: int | None = Field(
        default=None,
        ge=1,
        description="Skip reasoning when triple count exceeds this limit.",
    )
    max_connections: int = Field(default=1, ge=1)
    use_kuzu: bool = Field(default=False)
    kuzu_path: str = Field(default="kuzu.db")
    deterministic_node_budget: int | None = Field(
        default=None,
        ge=0,
        description=(
            "Optional deterministic cap on in-memory graph nodes. When provided "
            "it overrides the derived limit from the RAM budget."
        ),
    )
    minimum_deterministic_resident_nodes: int = Field(
        default=2,
        ge=2,
        description=(
            "Lower bound on nodes kept resident when RAM-based eviction falls back "
            "to deterministic limits."
        ),
    )

    _validate_rdf_backend = field_validator("rdf_backend")(validate_rdf_backend)


class AgentConfig(BaseModel):
    """Configuration for a single agent."""

    enabled: bool = Field(default=True)
    model: Optional[str] = None
    preferred_models: List[str] = Field(
        default_factory=list,
        description="Ordered list of models preferred for this agent",
    )
    allowed_models: List[str] = Field(
        default_factory=list,
        description="Allowlist restricting which models may be selected",
    )
    token_share: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Fraction of the global token budget reserved for the agent",
    )
    latency_slo_ms: float | None = Field(
        default=None,
        ge=0.0,
        description="Agent-specific latency objective in milliseconds",
    )


class APIConfig(BaseModel):
    """Configuration for HTTP API behaviour."""

    webhooks: List[str] = Field(default_factory=list)
    webhook_timeout: int = Field(default=5, ge=1)
    webhook_retries: int = Field(default=3, ge=0)
    webhook_backoff: float = Field(default=0.5, ge=0.0)
    api_key: str | None = Field(
        default=None,
        description="Shared secret required in the X-API-Key header when set",
    )
    api_keys: Dict[str, str] = Field(
        default_factory=dict,
        description="Optional mapping of API keys to roles",
    )
    role_permissions: Dict[str, List[str]] = Field(
        default_factory=lambda: {
            "anonymous": ["query", "docs"],
            "user": ["query", "docs"],
            "admin": [
                "query",
                "docs",
                "metrics",
                "capabilities",
                "config",
                "health",
            ],
        },
        description="Mapping of roles to allowed actions",
    )
    bearer_token: str | None = Field(
        default=None,
        description="Token required in the Authorization header when set",
    )
    rate_limit: int = Field(
        default=0,
        ge=0,
        description="Requests per minute allowed per client IP",
    )
    monitoring_enabled: bool = Field(
        default=False,
        description="Expose Prometheus metrics at /metrics",
    )


class DistributedConfig(BaseModel):
    """Configuration for distributed agent execution using Ray."""

    enabled: bool = Field(default=False)
    address: str | None = Field(default=None, description="Ray cluster address")
    num_cpus: int = Field(default=1, ge=1)
    message_broker: str = Field(default="memory")
    broker_url: str | None = Field(default=None, description="URL for the message broker")


class AnalysisConfig(BaseModel):
    """Configuration for data analysis features."""

    polars_enabled: bool = Field(default=False)


class ConfigModel(BaseModel):
    """Main configuration model with validation."""

    backend: str = Field(default="lmstudio")
    llm_backend: str = Field(default="lmstudio")
    llm_pool_size: int = Field(default=2, ge=1)
    loops: int = Field(default=2, ge=1)
    ram_budget_mb: int = Field(default=1024, ge=0)
    token_budget: Optional[int] = Field(
        default=None,
        ge=1,
        description="Maximum tokens available for a single run",
    )
    adaptive_max_factor: int = Field(
        default=20,
        ge=1,
        description="Maximum multiple of query tokens for adaptive budgeting",
    )
    adaptive_min_buffer: int = Field(
        default=10,
        ge=0,
        description="Minimum token buffer added when using adaptive budgeting",
    )
    circuit_breaker_threshold: int = Field(
        default=3,
        ge=1,
        description="Failure count before a circuit opens",
    )
    circuit_breaker_cooldown: int = Field(
        default=30,
        ge=1,
        description="Cooldown in seconds before attempting recovery",
    )
    max_errors: int = Field(
        default=3,
        ge=1,
        description="Abort reasoning after this many errors",
    )
    agents: List[str] = Field(default=["Synthesizer", "Contrarian", "FactChecker"])
    primus_start: int = Field(default=0)
    reasoning_mode: ReasoningMode = Field(default=ReasoningMode.DIALECTICAL)
    output_format: Optional[str] = None
    tracing_enabled: bool = Field(default=False)
    monitor_interval: float = Field(default=1.0, ge=0.1)
    cpu_warning_threshold: float = Field(default=80.0, ge=0.0, le=100.0)
    memory_warning_threshold: float = Field(default=80.0, ge=0.0, le=100.0)
    cpu_critical_threshold: float = Field(default=90.0, ge=0.0, le=100.0)
    memory_critical_threshold: float = Field(default=90.0, ge=0.0, le=100.0)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    agent_config: Dict[str, AgentConfig] = Field(default_factory=dict)
    search: SearchConfig = Field(default_factory=SearchConfig)
    api: APIConfig = Field(default_factory=APIConfig)
    analysis: AnalysisConfig = Field(default_factory=AnalysisConfig)
    model_routing: ModelRoutingConfig = Field(default_factory=ModelRoutingConfig)
    user_preferences: Dict[str, Any] = Field(default_factory=dict)
    enable_agent_messages: bool = Field(
        default=False,
        description="Allow agents to exchange messages during cycles",
    )
    enable_feedback: bool = Field(
        default=False,
        description="Enable cross-agent feedback messages",
    )
    coalitions: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Named coalitions of agents for message broadcasting",
    )
    gate_policy_enabled: bool = Field(
        default=True,
        description="Enable scout gate heuristics before dialectical debate",
    )
    gate_retrieval_overlap_threshold: float = Field(
        default=0.6,
        ge=0.0,
        le=1.0,
        description="Minimum overlap that still triggers debate for scout evidence",
    )
    gate_nli_conflict_threshold: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Contradiction probability that forces multi-loop debate",
    )
    gate_complexity_threshold: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Complexity score that escalates to full debate",
    )
    gate_coverage_gap_threshold: float = Field(
        default=0.25,
        ge=0.0,
        le=1.0,
        description="Maximum uncovered-claim share before debate escalates",
    )
    gate_retrieval_confidence_threshold: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Minimum retrieval confidence required to skip debate",
    )
    gate_graph_contradiction_threshold: float = Field(
        default=0.25,
        ge=0.0,
        le=1.0,
        description=(
            "Weighted contradiction score from the knowledge graph that triggers debate."
        ),
    )
    gate_graph_similarity_threshold: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description=(
            "Minimum weighted graph similarity signal required to skip multi-loop debate."
        ),
    )
    gate_scout_agreement_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description=(
            "Minimum agreement score among scout samples required to skip debate."
        ),
    )
    gate_user_overrides: Dict[str, Any] = Field(
        default_factory=dict,
        description="Optional overrides for gate policy decisions and signals",
    )
    auto_scout_samples: int = Field(
        default=2,
        ge=0,
        description=(
            "Number of additional fast Synthesizer samples gathered during AUTO scout "
            "mode before evaluating the gate."
        ),
    )
    graph_eviction_policy: str = Field(
        default="LRU",
        description=(
            "Policy for evicting nodes from the knowledge graph. Supported "
            'policies: "LRU", "score", "hybrid", "priority", "adaptive"'
        ),
    )
    default_model: str = Field(default="mistral")
    active_profile: Optional[str] = None
    distributed: bool = Field(
        default=False,
        description="Run agents in distributed mode (multiprocessing or remote)",
    )
    distributed_config: DistributedConfig = Field(default_factory=DistributedConfig)

    _validate_reasoning_mode = field_validator("reasoning_mode", mode="before")(
        validate_reasoning_mode
    )
    _validate_token_budget = field_validator("token_budget", mode="before")(validate_token_budget)
    _validate_eviction_policy = field_validator("graph_eviction_policy", mode="before")(
        validate_eviction_policy
    )

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ConfigModel":
        try:
            return cls(**data)
        except ValidationError:
            model = cls()
            for field, value in data.items():
                if field in cls.model_fields:
                    try:
                        setattr(model, field, value)
                    except Exception:  # pragma: no cover - ignore bad fields
                        continue
            return model

    def model_copy(
        self,
        *,
        update: Mapping[str, Any] | None = None,
        deep: bool = False,
    ) -> Self:
        """Return a cloned configuration while preserving ``ConfigModel`` typing."""

        base_model = cast(Any, super(ConfigModel, self))
        return cast(Self, base_model.model_copy(update=update, deep=deep))

    model_config: ClassVar[SettingsConfigDict] = {"extra": "ignore"}
