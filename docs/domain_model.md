# Domain Model

This document maps the core bounded contexts in Autoresearch and their
relationships.

## Agents

Agents drive the dialectical reasoning cycle. Each agent implements the base
interface and uses prompts and models defined in `AgentConfig`.

- Spec: documented in `docs/specs/agents.md`
- Code: `src/autoresearch/agents/base.py`

## Queries

Queries define user intent and orchestrator responses. `QueryRequest` captures
incoming parameters, while `QueryResponse` records final answers.

- Spec: documented in `docs/specs/models.md`
- Code: `src/autoresearch/models.py`

## Storage

Storage persists claims and supports graph and vector retrieval via a unified
`StorageManager` over NetworkX, DuckDB, and RDFLib backends.

- Spec: documented in `docs/specs/storage.md`
- Code: `src/autoresearch/storage.py`

## Search

Search generates query variants and federates lookups across registered
backends, caching results and ranking sources. The hierarchical pipeline
described in
[System Specification §6](specification.md#6-search)
adds semantic tree nodes, traversal summaries, and calibrated path scores as
first-class artefacts. These records flow into Storage for GraphRAG ingestion
and are consumed by agents that subscribe to scout-gate signals.

See the [hierarchical retrieval overview](specs/search.md#hierarchical-traversal)
diagram for an end-to-end view of offline construction, calibrated traversal,
and the dynamic corpus fallback loop.

- Spec: documented in `docs/specs/search.md`
- Code: `src/autoresearch/search/core.py`
- Configuration: `ContextAwareSearchConfig` in
  `docs/specs/config.md#contextawaresearchconfig`

## Relationships

- Agents create `QueryRequest` objects and consume `QueryResponse` results.
- Search uses queries to gather data and may persist findings through Storage.
- Storage indexes content that Search retrieves and ranks.
- Agents rely on Search for external knowledge and on Storage for accumulated
  claims.

