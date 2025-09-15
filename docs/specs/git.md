# Git Utilities

## Overview

Lightweight stub of the `git` package and search helpers used for tests.

## Algorithms

- `Repo` simulates commit history and minimal Git operations.
- `GitSearcher` indexes files and commit messages for substring search.

## Invariants

- `Repo.head.commit` always reflects the latest commit.
- Search results list paths and line numbers in sorted order.

## Proof Sketch

Unit tests create repositories and validate commit traversal and search
output.

## Simulation Expectations

- `tests/unit/test_git_repo_stub.py` exercises repository creation and
  commit linkage.
- `tests/targeted/test_git_search.py` verifies search over files and commits.

## Traceability

- Code: [src/git/__init__.py][m1]<br>[src/git/search.py][m2]
- Tests: [tests/unit/test_git_repo_stub.py][t1]<br>[tests/targeted/test_git_search.py][t2]

[m1]: ../../src/git/__init__.py
[m2]: ../../src/git/search.py
[t1]: ../../tests/unit/test_git_repo_stub.py
[t2]: ../../tests/targeted/test_git_search.py
