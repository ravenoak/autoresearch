# CLI testing helpers

When writing CLI tests, avoid real storage initialisation by using the
`dummy_storage` fixture. It registers a minimal `autoresearch.storage` module
and provides a no-op `StorageManager.setup`.

Use the fixture with `pytest.mark.usefixtures("dummy_storage")` at the module
level or by including it as a parameter in individual tests. Import the CLI
entry point only after applying the fixture:

```
import importlib

pytestmark = pytest.mark.usefixtures("dummy_storage")

app = importlib.import_module("autoresearch.main").app
```

This ensures storage calls are isolated and keeps CLI tests fast and
deterministic.

## Backup restore errors

The `backup restore` command reports clearer failures when archives are
missing or corrupted.

- Missing paths show `Invalid backup path: <path> does not exist`.
- Corrupted archives surface `Error restoring backup: Corrupted backup archive`.

Use these messages when asserting restore behaviour in tests.
