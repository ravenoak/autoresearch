"""Evaluation harness for curated truthfulness benchmarks."""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, List, Mapping, Optional, Sequence
from uuid import uuid4

import duckdb

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
    recorded_at: datetime = field(
        default_factory=lambda: datetime.now(tz=timezone.utc)
    )
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass
class EvaluationSummary:
    """Aggregated metrics for a benchmark run."""

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
    config_signature: str
    duckdb_path: Optional[Path]
    example_parquet: Optional[Path]
    summary_parquet: Optional[Path]


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
            response = runner(example.prompt, config.model_copy(deep=True))
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
        total_tokens = execution_metrics.get("total_tokens", {})
        citations = response.citations or []
        claim_audits = response.claim_audits or []
        contradiction = self._has_contradiction(claim_audits)
        answer = response.answer

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
            metadata={
                "example_metadata": example.metadata,
                "claim_audits": claim_audits,
                "raw_metrics": execution_metrics,
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

        example_parquet: Optional[Path] = None
        summary_parquet: Optional[Path] = None

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
                config_signature,
            )
        if store_parquet:
            example_parquet, summary_parquet = self._export_parquet(run_id)
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
            config_signature=config_signature,
            duckdb_path=self.duckdb_path if store_duckdb else None,
            example_parquet=example_parquet,
            summary_parquet=summary_parquet,
        )

    def _ensure_duckdb_schema(self) -> None:
        with duckdb.connect(self._duckdb_uri()) as conn:
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
                    metadata JSON,
                    recorded_at TIMESTAMP,
                    config_signature VARCHAR
                )
                """
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
                    config_signature VARCHAR
                )
                """
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
                json.dumps(result.metadata, default=str),
                result.recorded_at,
                config_signature,
            )
            for result in results
        ]
        insert_sql = (
            "INSERT INTO evaluation_results VALUES ("
            "?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
        )
        with duckdb.connect(self._duckdb_uri()) as conn:
            conn.executemany(insert_sql, rows)

    def _purge_run(self, run_id: str) -> None:
        with duckdb.connect(self._duckdb_uri()) as conn:
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
        config_signature: str,
    ) -> None:
        insert_sql = (
            "INSERT INTO evaluation_run_summary VALUES ("
            "?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
        )
        with duckdb.connect(self._duckdb_uri()) as conn:
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
                    config_signature,
                ),
            )

    def _export_parquet(self, run_id: str) -> tuple[Path, Path]:
        timestamp = datetime.now(tz=timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        example_parquet = self.output_dir / f"{run_id}_examples_{timestamp}.parquet"
        summary_parquet = self.output_dir / f"{run_id}_summary_{timestamp}.parquet"
        with duckdb.connect(self._duckdb_uri()) as conn:
            sanitized_examples = str(example_parquet).replace("'", "''")
            sanitized_summary = str(summary_parquet).replace("'", "''")
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
        return example_parquet, summary_parquet

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

    def _duckdb_uri(self) -> str:
        return str(self.duckdb_path)
