# Git Search Specification

## Overview

The Git search module indexes repository content and commit history to support
simple substring queries. It crawls the working tree, captures text from tracked
files, and records commit messages for later lookup.

## Repository Crawling

- Traverse the repository root recursively.
- Ignore files that fail UTF-8 decoding.
- Store each text file as a list of lines keyed by its relative path.
- Record commit messages in reverse chronological order.

## Query Semantics

- Searches are case-insensitive substring matches.
- File hits return the relative path, line number, and matching line.
- Commit hits return the commit message with no path or line metadata.
- Results are ordered by path, then line number, followed by commit messages.

## Invariants

- Indexing reads only the working tree; bare repositories are unsupported.
- Binary files remain unindexed and cannot surface in results.
- Duplicate queries yield stable output given an unchanged repository.

## Algorithms

- Indexing performs a depth-first scan over tracked text files.
- Querying runs a case-insensitive substring search on stored lines and commits.
- Results merge file hits and commit messages in path then line order.

## Proof Sketch

- Every tracked text line and commit message is stored during indexing.
- A query matches exactly when its lowercase form exists in the stored corpus.
- Therefore a search returns all and only occurrences of the query string.

## Simulation Expectations

- Binary files are skipped and never appear in output.
- Re-running the indexer on unchanged data yields identical search results.
- Query latency scales linearly with repository size.
