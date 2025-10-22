# Scholarly Ingestion Guide

The scholarly connectors allow workspaces to capture arXiv and Hugging Face
Papers content for offline research. This guide explains how to fetch papers,
verify cached metadata, and attach sources to workspace manifests from both the
CLI and desktop UI.

## Prerequisites

- Ensure the Autoresearch CLI is installed and configured (`autoresearch
  config init`).
- Initialise storage so DuckDB tables and cache directories exist (`autoresearch
  workspace list`).
- Optional: activate a workspace before running the commands below.

## CLI Workflow

1. Search for papers using multiple providers:

   ```bash
   autoresearch workspace papers search "retrieval augmented generation" \
       --provider arxiv --provider huggingface
   ```

   The CLI prints the top matches grouped by provider with the normalised
   identifier that can be used during ingestion.

2. Ingest a paper and cache its metadata and body:

   ```bash
   autoresearch workspace papers ingest arxiv 2401.01234v1 --workspace audit-notes
   ```

   The command downloads the abstract, stores it under a deterministic path in
   `scholarly_cache/`, and persists provenance (source URL, checksum, content
   type, retrieval timestamp) to DuckDB.

3. Attach a cached paper to the active workspace manifest:

   ```bash
   autoresearch workspace papers attach audit-notes arxiv 2401.01234v1
   ```

   Each attached resource carries the cache path and provenance data so debates
   can cite the content while offline.

## Desktop Workflow

- Use the **Resources → Search Scholarly Papers…** menu to run provider queries
  without leaving the desktop client.
- Select **Ingest Scholarly Paper…** to cache a DOI or arXiv identifier. When a
  workspace is active, the UI prompts to attach the paper immediately.
- Choose **Attach Cached Paper…** to browse previously ingested items for the
  current workspace.

## Offline Replay

Once a paper has been cached the metadata lives in the `scholarly_papers`
DuckDB table. Behaviour tests verify that disconnecting from the network still
allows the agent to surface cached content and cite the preserved provenance.
Check the `provenance.retrieved_at` timestamp to confirm the last sync time.
