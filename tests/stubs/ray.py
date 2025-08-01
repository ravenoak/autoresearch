"""Stub implementation of the :mod:`ray` package used in tests."""

import sys
import types

if "ray" not in sys.modules:
    def _remote(func):
        return types.SimpleNamespace(remote=lambda *a, **k: func(*a, **k))

    ray_stub = types.SimpleNamespace(
        init=lambda *a, **k: None,
        shutdown=lambda *a, **k: None,
        remote=_remote,
        get=lambda x: x,
        put=lambda x: x,
        ObjectRef=object,
    )
    sys.modules["ray"] = ray_stub
    dag_mod = types.ModuleType("ray.dag")
    compiled = types.ModuleType("ray.dag.compiled_dag_node")
    compiled._shutdown_all_compiled_dags = lambda: None
    sys.modules.setdefault("ray.dag", dag_mod)
    sys.modules.setdefault("ray.dag.compiled_dag_node", compiled)
    ray_stub.dag = dag_mod
