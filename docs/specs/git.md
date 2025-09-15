# Git Stub

## Overview

The `git` package offers a lightweight stub of GitPython used during tests. It
provides minimal repository manipulation and search hooks without requiring the
real dependency.

## Algorithms

- `Repo.init(path)` creates a repository directory and registers a singleton
  instance per path.
- `Repo.Index.commit` appends a commit and moves `HEAD` to the new commit.
- `Repo.iter_commits` yields commits newest first, honoring `max_count`.
- Context manager methods allow `with Repo(...)` usage.

## Invariants

- Each repository path maps to a single `Repo` instance.
- Commits form a linked parent chain.
- `head` raises `AttributeError` if no commits exist.

## Proof Sketch

Integration tests such as `tests/integration/test_local_git_backend.py` and
targeted tests like `tests/targeted/test_git_search.py` exercise commit creation
and iteration, confirming the invariants.

## Simulation Expectations

- Initializing a repo and committing should expose the commit via
  `iter_commits()`.
- Accessing `Repo.head` before any commit raises `AttributeError`.

## Traceability

- Code: [src/git/__init__.py][m1]
- Tests:
  - [tests/integration/test_local_git_backend.py][t1]
  - [tests/targeted/test_git_search.py][t2]

[m1]: ../../src/git/__init__.py
[t1]: ../../tests/integration/test_local_git_backend.py
[t2]: ../../tests/targeted/test_git_search.py
