import sys
import types


def test_shutdown_without_start():
    """RayExecutor.shutdown should handle cases with no brokers."""

    # Provide lightweight stubs for heavy optional dependencies
    sys.modules.setdefault("sentence_transformers", types.SimpleNamespace(SentenceTransformer=object))
    sys.modules.setdefault("transformers", types.SimpleNamespace())
    sys.modules.setdefault("torch", types.SimpleNamespace())

    def _remote(func):
        return types.SimpleNamespace(remote=lambda *a, **k: func(*a, **k))

    sys.modules.setdefault(
        "ray",
        types.SimpleNamespace(
            init=lambda *a, **k: None,
            shutdown=lambda *a, **k: None,
            remote=_remote,
            get=lambda x: x,
            put=lambda x: x,
            ObjectRef=object,
        ),
    )

    from autoresearch.distributed import RayExecutor
    from autoresearch.config.models import ConfigModel, DistributedConfig

    cfg = ConfigModel(distributed=False, distributed_config=DistributedConfig(enabled=False))
    executor = RayExecutor(cfg)

    # Should exit cleanly without raising exceptions
    executor.shutdown()
