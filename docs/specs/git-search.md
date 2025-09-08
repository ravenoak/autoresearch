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

## Traceability

- Modules
  - [src/git/search.py](../../src/git/search.py)
- Tests
  - [tests/targeted/test_git_search.py](../../tests/targeted/test_git_search.py)
