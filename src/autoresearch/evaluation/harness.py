"""Evaluation harness for curated truthfulness benchmarks."""

from __future__ import annotations

import hashlib
import json
import logging
from contextlib import closing, contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Iterator, List, Mapping, Optional, Sequence, cast
from uuid import uuid4

import duckdb
from duckdb import DuckDBPyConnection

from ..config.models import ConfigModel
from ..models import QueryResponse
from .datasets import EvaluationExample, available_datasets, load_examples

log = logging.getLogger(__name__)

Runner = Callable[[str, ConfigModel], QueryResponse]


@dataclass
class ExampleResult:
    """Per-example evaluation metrics for a single benchmark prompt."""

    dataset: str
    example_id: str
    prompt: str
    expected_answers: Sequence[str]
    answer: Optional[str] = None
    correct: Optional[bool] = None
    has_citations: Optional[bool] = None
    citation_count: Optional[int] = None
    contradiction: Optional[bool] = None
    latency_seconds: Optional[float] = None
    tokens_input: Optional[int] = None
    tokens_output: Optional[int] = None
    tokens_total: Optional[int] = None
    cycles_completed: Optional[int] = None
    gate_should_debate: Optional[bool] = None
    planner_depth: Optional[float] = None
    routing_delta: Optional[float] = None
    routing_decision_count: Optional[int] = None
    gate_events: Sequence[Mapping[str, Any]] = field(default_factory=list)
    routing_strategy: Optional[str] = None
    recorded_at: datetime = field(
        default_factory=lambda: datetime.now(tz=timezone.utc)
    )
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass
class EvaluationSummary:
    """Aggregated metrics for a benchmark run.

    Captures accuracy, citation coverage, contradiction rate, latency, token
    usage, and loop/gating telemetry so longitudinal analyses can surface
    regressions in control flow policies.
    """

    dataset: str
    run_id: str
    started_at: datetime
    completed_at: datetime
    total_examples: int
    accuracy: Optional[float]
    citation_coverage: Optional[float]
    contradiction_rate: Optional[float]
    avg_latency_seconds: Optional[float]
    avg_tokens_input: Optional[float]
    avg_tokens_output: Optional[float]
    avg_tokens_total: Optional[float]
    avg_cycles_completed: Optional[float]
    gate_debate_rate: Optional[float]
    gate_exit_rate: Optional[float]
    gated_example_ratio: Optional[float]
    avg_planner_depth: Optional[float]
    avg_routing_delta: Optional[float]
    total_routing_delta: Optional[float]
    avg_routing_decisions: Optional[float]
    routing_strategy: Optional[str]
    config_signature: str
    duckdb_path: Optional[Path]
    example_parquet: Optional[Path]
    summary_parquet: Optional[Path]
    example_csv: Optional[Path]
    summary_csv: Optional[Path]


@dataclass
class RoutingStrategyComparison:
    """Delta between two routing strategies on a single dataset."""

    dataset: str
    baseline_strategy: str
    variant_strategy: str
    accuracy_delta: Optional[float]
    routing_delta_diff: Optional[float]
    latency_delta: Optional[float]
    tokens_delta: Optional[float]


class EvaluationHarness:
    """Execute curated truthfulness benchmarks and persist metrics."""

    def __init__(
        self,
        *,
        output_dir: Path | str | None = None,
        duckdb_path: Path | str | None = None,
        runner: Runner | None = None,
    ) -> None:
        self.output_dir = Path(output_dir or "baseline/evaluation")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.duckdb_path = Path(duckdb_path or self.output_dir / "truthfulness.duckdb")
        self._runner = runner

    def run(
        self,
        datasets: Sequence[str],
        *,
        config: ConfigModel,
        limit: Optional[int] = None,
        dry_run: bool = False,
        store_duckdb: bool = True,
        store_parquet: bool = True,
    ) -> List[EvaluationSummary]:
        """Run the evaluation harness for ``datasets``.

        Args:
            datasets: Iterable of dataset identifiers.
            config: Active configuration used for orchestration runs.
            limit: Optional per-dataset cap on processed examples.
            dry_run: Skip orchestrator execution when ``True``.
            store_duckdb: Persist metrics to DuckDB when ``True``.
            store_parquet: Export metrics to Parquet files when ``True``.

        Returns:
            List of :class:`EvaluationSummary` entries (one per dataset).

        Raises:
            ValueError: If ``datasets`` is empty or contains an unknown identifier.
        """

        if not datasets:
            raise ValueError("At least one dataset must be specified")

        summaries: List[EvaluationSummary] = []
        normalized = self._normalise_datasets(datasets)
        config_signature = self._config_signature(config)

        for dataset in normalized:
            examples = list(load_examples(dataset))
            if limit is not None:
                examples = examples[: max(limit, 0)]
            if not examples:
                log.warning("Dataset %s has no examples after applying limit", dataset)
                continue
            started_at = datetime.now(tz=timezone.utc)
            results = self._execute_dataset(
                dataset,
                examples,
                config=config,
                dry_run=dry_run,
            )
            completed_at = datetime.now(tz=timezone.utc)
            summary = self._summarise(
                dataset,
                results,
                run_id=self._build_run_id(dataset, started_at),
                started_at=started_at,
                completed_at=completed_at,
                config_signature=config_signature,
                store_duckdb=store_duckdb,
                store_parquet=store_parquet,
            )
            summaries.append(summary)
        return summaries

    def _execute_dataset(
        self,
        dataset: str,
        examples: Sequence[EvaluationExample],
        *,
        config: ConfigModel,
        dry_run: bool,
    ) -> List[ExampleResult]:
        results: List[ExampleResult] = []
        runner = self._runner or self._default_runner(config)

        for example in examples:
            if dry_run:
                results.append(
                    ExampleResult(
                        dataset=dataset,
                        example_id=example.example_id,
                        prompt=example.prompt,
                        expected_answers=example.expected_answers,
                        metadata=example.metadata,
                    )
                )
                continue
            config_copy = config.model_copy(update={}, deep=True)
            response = runner(example.prompt, config_copy)
            results.append(self._build_result(example, response))
        return results

    def _default_runner(self, config: ConfigModel) -> Runner:
        from ..orchestration.orchestrator import Orchestrator

        orchestrator = Orchestrator()

        def _run(query: str, cfg: ConfigModel) -> QueryResponse:
            return orchestrator.run_query(query, cfg)

        return _run

    def _build_result(
        self,
        example: EvaluationExample,
        response: QueryResponse,
    ) -> ExampleResult:
        metrics = response.metrics or {}
        execution_metrics = metrics.get("execution_metrics", {})
        gate_events_raw = metrics.get("gate_events") or []
        total_tokens = execution_metrics.get("total_tokens", {})
        citations = response.citations or []
        claim_audits = response.claim_audits or []
        contradiction = self._has_contradiction(claim_audits)
        answer = response.answer

        cycles_completed = execution_metrics.get("cycles_completed")
        if isinstance(cycles_completed, float):
            cycles_completed = int(cycles_completed)
        elif cycles_completed is not None and not isinstance(cycles_completed, int):
            try:
                cycles_completed = int(cycles_completed)
            except (TypeError, ValueError):
                cycles_completed = None

        gate_should_debate: Optional[bool]
        gate_should_debate = None
        if gate_events_raw:
            final_event = gate_events_raw[-1]
            decision = final_event.get("should_debate")
            if isinstance(decision, bool):
                gate_should_debate = decision

        planner_depth = self._planner_depth(response)
        routing_delta, routing_decision_count = self._routing_metrics(
            execution_metrics
        )
        routing_strategy = execution_metrics.get("model_routing_strategy")

        result = ExampleResult(
            dataset=example.dataset,
            example_id=example.example_id,
            prompt=example.prompt,
            expected_answers=example.expected_answers,
            answer=answer,
            correct=self._is_correct(answer, example.expected_answers),
            has_citations=bool(citations),
            citation_count=len(citations) if citations else 0,
            contradiction=contradiction,
            latency_seconds=execution_metrics.get("total_duration_seconds"),
            tokens_input=total_tokens.get("input"),
            tokens_output=total_tokens.get("output"),
            tokens_total=total_tokens.get("total"),
            cycles_completed=cycles_completed,
            gate_should_debate=gate_should_debate,
            planner_depth=planner_depth,
            routing_delta=routing_delta,
            routing_decision_count=routing_decision_count,
            gate_events=gate_events_raw,
            routing_strategy=routing_strategy,
            metadata={
                "example_metadata": example.metadata,
                "claim_audits": claim_audits,
                "raw_metrics": execution_metrics,
                "gate_events": gate_events_raw,
            },
        )
        return result

    def _summarise(
        self,
        dataset: str,
        results: Sequence[ExampleResult],
        *,
        run_id: str,
        started_at: datetime,
        completed_at: datetime,
        config_signature: str,
        store_duckdb: bool,
        store_parquet: bool,
    ) -> EvaluationSummary:
        accuracy = self._mean_boolean([r.correct for r in results])
        citation_coverage = self._mean_boolean([r.has_citations for r in results])
        contradiction_rate = self._mean_boolean([r.contradiction for r in results])
        avg_latency = self._mean_float([r.latency_seconds for r in results])
        avg_tokens_in = self._mean_float([r.tokens_input for r in results])
        avg_tokens_out = self._mean_float([r.tokens_output for r in results])
        avg_tokens_total = self._mean_float([r.tokens_total for r in results])
        avg_cycles_completed = self._mean_float(
            [float(r.cycles_completed) if r.cycles_completed is not None else None for r in results]
        )
        avg_planner_depth = self._mean_float([r.planner_depth for r in results])
        avg_routing_delta = self._mean_float([r.routing_delta for r in results])
        total_routing_delta = self._sum_float([r.routing_delta for r in results])
        avg_routing_decisions = self._mean_float(
            [
                float(r.routing_decision_count)
                if r.routing_decision_count is not None
                else None
                for r in results
            ]
        )
        routing_strategy = next(
            (
                result.routing_strategy
                for result in results
                if result.routing_strategy
            ),
            None,
        )

        gate_decisions = [r.gate_should_debate for r in results if r.gate_should_debate is not None]
        gated_examples = len(gate_decisions)
        gate_debate_rate = None
        gate_exit_rate = None
        if gated_examples:
            debate_count = sum(1 for decision in gate_decisions if decision)
            gate_debate_rate = debate_count / gated_examples
            gate_exit_rate = (gated_examples - debate_count) / gated_examples
        gated_example_ratio = (gated_examples / len(results)) if results else None

        example_parquet: Optional[Path] = None
        summary_parquet: Optional[Path] = None
        example_csv: Optional[Path] = None
        summary_csv: Optional[Path] = None

        needs_persistence = store_duckdb or store_parquet
        if needs_persistence:
            self._ensure_duckdb_schema()
            self._persist_examples(run_id, config_signature, results)
            self._persist_summary(
                run_id,
                dataset,
                started_at,
                completed_at,
                len(results),
                accuracy,
                citation_coverage,
                contradiction_rate,
                avg_latency,
                avg_tokens_in,
                avg_tokens_out,
                avg_tokens_total,
                avg_cycles_completed,
                gate_debate_rate,
                gate_exit_rate,
                gated_example_ratio,
                avg_planner_depth,
                avg_routing_delta,
                total_routing_delta,
                avg_routing_decisions,
                routing_strategy,
                config_signature,
            )
        if store_parquet:
            (
                example_parquet,
                summary_parquet,
                example_csv,
                summary_csv,
            ) = self._export_artifacts(run_id)
        if needs_persistence and not store_duckdb:
            self._purge_run(run_id)

        return EvaluationSummary(
            dataset=dataset,
            run_id=run_id,
            started_at=started_at,
            completed_at=completed_at,
            total_examples=len(results),
            accuracy=accuracy,
            citation_coverage=citation_coverage,
            contradiction_rate=contradiction_rate,
            avg_latency_seconds=avg_latency,
            avg_tokens_input=avg_tokens_in,
            avg_tokens_output=avg_tokens_out,
            avg_tokens_total=avg_tokens_total,
            avg_cycles_completed=avg_cycles_completed,
            gate_debate_rate=gate_debate_rate,
            gate_exit_rate=gate_exit_rate,
            gated_example_ratio=gated_example_ratio,
            avg_planner_depth=avg_planner_depth,
            avg_routing_delta=avg_routing_delta,
            total_routing_delta=total_routing_delta,
            avg_routing_decisions=avg_routing_decisions,
            routing_strategy=routing_strategy,
            config_signature=config_signature,
            duckdb_path=self.duckdb_path if store_duckdb else None,
            example_parquet=example_parquet,
            summary_parquet=summary_parquet,
            example_csv=example_csv,
            summary_csv=summary_csv,
        )

    def _ensure_duckdb_schema(self) -> None:
        with self._open_duckdb() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS evaluation_results (
                    run_id VARCHAR,
                    dataset VARCHAR,
                    example_id VARCHAR,
                    prompt VARCHAR,
                    answer VARCHAR,
                    expected_answers VARCHAR,
                    is_correct BOOLEAN,
                    has_citations BOOLEAN,
                    citation_count INTEGER,
                    contradiction BOOLEAN,
                    latency_seconds DOUBLE,
                    tokens_input BIGINT,
                    tokens_output BIGINT,
                    tokens_total BIGINT,
                    cycles_completed INTEGER,
                    gate_should_debate BOOLEAN,
                    planner_depth DOUBLE,
                    routing_delta DOUBLE,
                    routing_decision_count INTEGER,
                    gate_events JSON,
                    metadata JSON,
                    recorded_at TIMESTAMP,
                    routing_strategy VARCHAR,
                    config_signature VARCHAR
                )
                """
            )
            conn.execute(
                "ALTER TABLE evaluation_results ADD COLUMN IF NOT EXISTS cycles_completed INTEGER"
            )
            conn.execute(
                "ALTER TABLE evaluation_results ADD COLUMN IF NOT EXISTS gate_should_debate BOOLEAN"
            )
            conn.execute(
                "ALTER TABLE evaluation_results ADD COLUMN IF NOT EXISTS gate_events JSON"
            )
            conn.execute(
                "ALTER TABLE evaluation_results ADD COLUMN IF NOT EXISTS planner_depth DOUBLE"
            )
            conn.execute(
                "ALTER TABLE evaluation_results ADD COLUMN IF NOT EXISTS routing_delta DOUBLE"
            )
            conn.execute(
                "ALTER TABLE evaluation_results ADD COLUMN IF NOT EXISTS routing_decision_count INTEGER"
            )
            conn.execute(
                "ALTER TABLE evaluation_results ADD COLUMN IF NOT EXISTS routing_strategy VARCHAR"
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS evaluation_run_summary (
                    run_id VARCHAR,
                    dataset VARCHAR,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    total_examples INTEGER,
                    accuracy DOUBLE,
                    citation_coverage DOUBLE,
                    contradiction_rate DOUBLE,
                    avg_latency_seconds DOUBLE,
                    avg_tokens_input DOUBLE,
                    avg_tokens_output DOUBLE,
                    avg_tokens_total DOUBLE,
                    avg_cycles_completed DOUBLE,
                    gate_debate_rate DOUBLE,
                    gate_exit_rate DOUBLE,
                    gated_example_ratio DOUBLE,
                    avg_planner_depth DOUBLE,
                    avg_routing_delta DOUBLE,
                    total_routing_delta DOUBLE,
                    avg_routing_decisions DOUBLE,
                    routing_strategy VARCHAR,
                    config_signature VARCHAR
                )
                """
            )
            conn.execute(
                "ALTER TABLE evaluation_run_summary ADD COLUMN IF NOT EXISTS avg_cycles_completed DOUBLE"
            )
            conn.execute(
                "ALTER TABLE evaluation_run_summary ADD COLUMN IF NOT EXISTS gate_debate_rate DOUBLE"
            )
            conn.execute(
                "ALTER TABLE evaluation_run_summary ADD COLUMN IF NOT EXISTS gate_exit_rate DOUBLE"
            )
            conn.execute(
                "ALTER TABLE evaluation_run_summary ADD COLUMN IF NOT EXISTS gated_example_ratio DOUBLE"
            )
            conn.execute(
                "ALTER TABLE evaluation_run_summary ADD COLUMN IF NOT EXISTS avg_planner_depth DOUBLE"
            )
            conn.execute(
                "ALTER TABLE evaluation_run_summary ADD COLUMN IF NOT EXISTS avg_routing_delta DOUBLE"
            )
            conn.execute(
                "ALTER TABLE evaluation_run_summary ADD COLUMN IF NOT EXISTS total_routing_delta DOUBLE"
            )
            conn.execute(
                "ALTER TABLE evaluation_run_summary ADD COLUMN IF NOT EXISTS avg_routing_decisions DOUBLE"
            )
            conn.execute(
                "ALTER TABLE evaluation_run_summary ADD COLUMN IF NOT EXISTS routing_strategy VARCHAR"
            )

    def _persist_examples(
        self,
        run_id: str,
        config_signature: str,
        results: Sequence[ExampleResult],
    ) -> None:
        rows = [
            (
                run_id,
                result.dataset,
                result.example_id,
                result.prompt,
                result.answer or "",
                json.dumps(list(result.expected_answers)),
                result.correct,
                result.has_citations,
                result.citation_count,
                result.contradiction,
                result.latency_seconds,
                result.tokens_input,
                result.tokens_output,
                result.tokens_total,
                result.cycles_completed,
                result.gate_should_debate,
                result.planner_depth,
                result.routing_delta,
                result.routing_decision_count,
                json.dumps(result.gate_events, default=str),
                json.dumps(result.metadata, default=str),
                result.recorded_at,
                result.routing_strategy,
                config_signature,
            )
            for result in results
        ]
        insert_sql = (
            "INSERT INTO evaluation_results VALUES ("
            "?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
        )
        with self._open_duckdb() as conn:
            executemany = cast(Any, conn).executemany
            executemany(insert_sql, rows)

    def _purge_run(self, run_id: str) -> None:
        with self._open_duckdb() as conn:
            conn.execute(
                "DELETE FROM evaluation_results WHERE run_id = ?", [run_id]
            )
            conn.execute(
                "DELETE FROM evaluation_run_summary WHERE run_id = ?", [run_id]
            )

    def _persist_summary(
        self,
        run_id: str,
        dataset: str,
        started_at: datetime,
        completed_at: datetime,
        total_examples: int,
        accuracy: Optional[float],
        citation_coverage: Optional[float],
        contradiction_rate: Optional[float],
        avg_latency: Optional[float],
        avg_tokens_in: Optional[float],
        avg_tokens_out: Optional[float],
        avg_tokens_total: Optional[float],
        avg_cycles_completed: Optional[float],
        gate_debate_rate: Optional[float],
        gate_exit_rate: Optional[float],
        gated_example_ratio: Optional[float],
        avg_planner_depth: Optional[float],
        avg_routing_delta: Optional[float],
        total_routing_delta: Optional[float],
        avg_routing_decisions: Optional[float],
        routing_strategy: Optional[str],
        config_signature: str,
    ) -> None:
        insert_sql = (
            "INSERT INTO evaluation_run_summary VALUES ("
            "?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
        )
        with self._open_duckdb() as conn:
            conn.execute(
                insert_sql,
                (
                    run_id,
                    dataset,
                    started_at,
                    completed_at,
                    total_examples,
                    accuracy,
                    citation_coverage,
                    contradiction_rate,
                    avg_latency,
                    avg_tokens_in,
                    avg_tokens_out,
                    avg_tokens_total,
                    avg_cycles_completed,
                    gate_debate_rate,
                    gate_exit_rate,
                    gated_example_ratio,
                    avg_planner_depth,
                    avg_routing_delta,
                    total_routing_delta,
                    avg_routing_decisions,
                    routing_strategy,
                    config_signature,
                ),
            )

    def _export_artifacts(self, run_id: str) -> tuple[Path, Path, Path, Path]:
        timestamp = datetime.now(tz=timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        example_parquet = self.output_dir / f"{run_id}_examples_{timestamp}.parquet"
        summary_parquet = self.output_dir / f"{run_id}_summary_{timestamp}.parquet"
        example_csv = self.output_dir / f"{run_id}_examples_{timestamp}.csv"
        summary_csv = self.output_dir / f"{run_id}_summary_{timestamp}.csv"
        with self._open_duckdb() as conn:
            sanitized_examples = str(example_parquet).replace("'", "''")
            sanitized_summary = str(summary_parquet).replace("'", "''")
            sanitized_examples_csv = str(example_csv).replace("'", "''")
            sanitized_summary_csv = str(summary_csv).replace("'", "''")
            conn.execute(
                f"COPY (SELECT * FROM evaluation_results WHERE run_id = ?) "
                f"TO '{sanitized_examples}' (FORMAT PARQUET)",
                [run_id],
            )
            conn.execute(
                f"COPY (SELECT * FROM evaluation_run_summary WHERE run_id = ?) "
                f"TO '{sanitized_summary}' (FORMAT PARQUET)",
                [run_id],
            )
            conn.execute(
                f"COPY (SELECT * FROM evaluation_results WHERE run_id = ?) "
                f"TO '{sanitized_examples_csv}' (FORMAT CSV, HEADER TRUE)",
                [run_id],
            )
            conn.execute(
                f"COPY (SELECT * FROM evaluation_run_summary WHERE run_id = ?) "
                f"TO '{sanitized_summary_csv}' (FORMAT CSV, HEADER TRUE)",
                [run_id],
            )
        return example_parquet, summary_parquet, example_csv, summary_csv

    @staticmethod
    def _mean_boolean(values: Iterable[Optional[bool]]) -> Optional[float]:
        filtered = [1.0 if value else 0.0 for value in values if value is not None]
        if not filtered:
            return None
        return sum(filtered) / len(filtered)

    @staticmethod
    def _mean_float(values: Iterable[Optional[float]]) -> Optional[float]:
        filtered = [value for value in values if value is not None]
        if not filtered:
            return None
        return sum(filtered) / len(filtered)

    @staticmethod
    def _sum_float(values: Iterable[Optional[float]]) -> Optional[float]:
        filtered = [value for value in values if value is not None]
        if not filtered:
            return None
        return sum(filtered)

    @staticmethod
    def compare_routing_strategies(
        baseline: Sequence[EvaluationSummary],
        variants: Sequence[EvaluationSummary],
    ) -> list[RoutingStrategyComparison]:
        """Compare routing accuracy and cost deltas across strategies."""

        def _delta(base_val: Optional[float], variant_val: Optional[float]) -> Optional[float]:
            if base_val is None or variant_val is None:
                return None
            return variant_val - base_val

        baseline_map = {summary.dataset: summary for summary in baseline}
        comparisons: list[RoutingStrategyComparison] = []
        for variant in variants:
            base = baseline_map.get(variant.dataset)
            if base is None:
                continue
            comparisons.append(
                RoutingStrategyComparison(
                    dataset=variant.dataset,
                    baseline_strategy=base.routing_strategy
                    or base.config_signature,
                    variant_strategy=variant.routing_strategy
                    or variant.config_signature,
                    accuracy_delta=_delta(base.accuracy, variant.accuracy),
                    routing_delta_diff=_delta(
                        base.total_routing_delta, variant.total_routing_delta
                    ),
                    latency_delta=_delta(
                        base.avg_latency_seconds, variant.avg_latency_seconds
                    ),
                    tokens_delta=_delta(
                        base.avg_tokens_total, variant.avg_tokens_total
                    ),
                )
            )
        return comparisons

    @staticmethod
    def _normalise_datasets(datasets: Sequence[str]) -> List[str]:
        known = {name.lower() for name in available_datasets()}
        normalised = []
        for dataset in datasets:
            lower = dataset.lower()
            if lower not in known:
                raise ValueError(f"Unknown dataset requested: {dataset}")
            normalised.append(lower)
        return normalised

    @staticmethod
    def _config_signature(config: ConfigModel) -> str:
        try:
            payload = config.model_dump(mode="json", exclude_none=True)
            serialised = json.dumps(payload, sort_keys=True)
        except Exception:  # pragma: no cover - defensive fall-back
            serialised = config.model_dump_json()
        digest = hashlib.sha256(serialised.encode("utf-8")).hexdigest()
        return digest[:16]

    @staticmethod
    def _build_run_id(dataset: str, started_at: datetime) -> str:
        token = uuid4().hex[:8]
        timestamp = started_at.strftime("%Y%m%dT%H%M%SZ")
        return f"{dataset}-{timestamp}-{token}"

    @staticmethod
    def _has_contradiction(claim_audits: Sequence[Mapping[str, Any]]) -> bool:
        contradiction_labels = {
            "refuted",
            "contradicted",
            "disputed",
            "unsupported",
            "fail",
        }
        for audit in claim_audits:
            status = str(audit.get("status", "")).strip().lower()
            if status in contradiction_labels:
                return True
        return False

    @staticmethod
    def _is_correct(answer: Optional[str], expected: Sequence[str]) -> Optional[bool]:
        if answer is None:
            return None
        normalized_answer = EvaluationHarness._normalise_text(answer)
        expected_set = {
            EvaluationHarness._normalise_text(candidate) for candidate in expected
        }
        if not expected_set:
            return None
        return normalized_answer in expected_set

    @staticmethod
    def _normalise_text(text: str) -> str:
        return " ".join(text.strip().lower().split())

    def _planner_depth(self, response: QueryResponse) -> Optional[float]:
        graph_payload: Any = getattr(response, "task_graph", None)
        if isinstance(graph_payload, Mapping):
            depth = self._task_graph_depth(graph_payload)
            if depth is not None:
                return depth
        metrics = getattr(response, "metrics", {})
        planner_meta = metrics.get("planner") if isinstance(metrics, Mapping) else None
        if isinstance(planner_meta, Mapping):
            telemetry = planner_meta.get("task_graph")
            if isinstance(telemetry, Mapping):
                depth_val = telemetry.get("max_depth") or telemetry.get("depth")
                if isinstance(depth_val, (int, float)):
                    return float(depth_val)
        return None

    def _task_graph_depth(self, payload: Mapping[str, Any]) -> Optional[float]:
        tasks_raw = payload.get("tasks")
        if not isinstance(tasks_raw, Sequence):
            return None
        nodes: dict[str, list[str]] = {}
        for entry in tasks_raw:
            if not isinstance(entry, Mapping):
                continue
            node_id = str(entry.get("id", "")).strip() or str(len(nodes))
            depends_raw = entry.get("depends_on")
            if isinstance(depends_raw, Sequence) and not isinstance(depends_raw, (str, bytes)):
                depends = [str(dep).strip() for dep in depends_raw if str(dep).strip()]
            else:
                depends = []
            nodes[node_id] = depends
        if not nodes:
            return None

        memo: dict[str, float] = {}

        def depth(node_id: str, trail: set[str]) -> float:
            if node_id in memo:
                return memo[node_id]
            if node_id in trail:
                return 1.0
            trail.add(node_id)
            dependencies = nodes.get(node_id, [])
            if not dependencies:
                memo[node_id] = 1.0
            else:
                memo[node_id] = 1.0 + max(
                    depth(dep, trail) for dep in dependencies if dep in nodes
                )
            trail.remove(node_id)
            return memo[node_id]

        try:
            max_depth = 0.0
            for node in nodes:
                depth_value = depth(node, cast(set[str], set()))
                if depth_value > max_depth:
                    max_depth = depth_value
            if max_depth == 0.0:
                return None
            return max_depth
        except ValueError:
            return None

    @staticmethod
    def _routing_metrics(
        execution_metrics: Mapping[str, Any]
    ) -> tuple[Optional[float], Optional[int]]:
        savings_meta = execution_metrics.get("model_routing_cost_savings")
        routing_delta: Optional[float] = None
        if isinstance(savings_meta, Mapping):
            total = savings_meta.get("total")
            try:
                routing_delta = float(cast(float | int | str, total))
            except (TypeError, ValueError):
                routing_delta = None
        decisions = execution_metrics.get("model_routing_decisions")
        routing_count: Optional[int] = None
        if isinstance(decisions, Sequence) and not isinstance(decisions, (str, bytes)):
            routing_count = len(decisions)
        return routing_delta, routing_count

    @contextmanager
    def _open_duckdb(self) -> Iterator[DuckDBPyConnection]:
        """Yield a DuckDB connection ensuring it is always closed."""

        with closing(duckdb.connect(self._duckdb_uri())) as connection:
            yield connection

    def _duckdb_uri(self) -> str:
        return str(self.duckdb_path)
