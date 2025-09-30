# Third-Party Stub Audit (Strict Mypy)

This note records the third-party import failures observed under
``mypy --strict`` and the shims introduced to unblock strict type checking.
It also captures the questions asked while validating that each shim mirrors
runtime behaviour.

- `pydantic`: Strict runs previously failed with ``Class cannot subclass
  "BaseModel"`` across models, agents, and API payloads because the package
  resolves to ``Any`` when site packages are hidden.【5cc994†L1-L44】
  【e50fee†L1-L93】
- `fastapi`/`starlette`: Middleware classes raised ``BaseHTTPMiddleware``
  subtype errors and request handlers became untyped because the framework
  resolved to ``Any`` without local type information.【5cc994†L1-L44】
- `requests`: HTTP helpers inside `search`, `llm`, and `test_tools` relied on
  ``requests`` but strict mode treated it as untyped, silencing parameter
  checks for ``Session`` usage.【085b5d†L1-L23】
- `psutil`/`pynvml`: Resource monitors imported these modules with unused
  ``type: ignore`` markers to placate missing stubs, preventing strict runs
  from validating CPU and GPU metric helpers.【5cc994†L1-L44】
- `spacy`, `sentence_transformers`, `bertopic`, `pdfminer.layout`,
  `fastembed.text`, and `owlrl` were guarded behind ``type: ignore`` comments
  despite local fallbacks, leaving context-aware search paths unchecked.
- `fastmcp`, `dspy`, and `PIL.Image` previously triggered
  ``import-not-found`` errors under ``mypy --strict`` because the repo relied
  on optional extras for runtime behaviour without local shims.

## Shim design and validation prompts

- For `pydantic` we asked whether ``BaseModel`` instances in the project call
  ``model_dump``, ``model_dump_json``, and ``model_validate`` in the same ways
  the real library allows. A runtime smoke check confirmed those methods and
  attribute shapes (`model_fields`, `model_fields_set`) behave as assumed, so
  the stub exposes the same signatures.【953c8b†L1-L32】
- We confirmed `ValidationError.errors()` returns a list of dicts that surface
  validation problems, matching our stub's structure.【92cc72†L1-L10】
- For `fastapi` and `starlette` the key question was whether middleware and
  router decorators need more than constructor signatures. Inspecting
  `routing.create_app` showed we only rely on ``add_middleware``,
  ``include_router``, and basic request state attributes, which the stub now
  mirrors.【5dc50d†L1-L52】【aaf952†L1-L120】
- `requests` usage centres on ``Session.get/post``, ``HTTPAdapter``, and
  ``Response.json``. The stub captures those call sites so strict checking can
  validate the surrounding retry logic.【085b5d†L1-L23】
- For `psutil` we verified that call sites only read ``cpu_percent``,
  ``virtual_memory().percent``, and ``Process().memory_info().rss``, allowing a
  compact stub that preserves those attributes while keeping optional fallbacks
  intact.【81b965†L49-L66】【800ff7†L108-L120】
- Optional NLP extras (`spacy`, `sentence_transformers`, `bertopic`) were
  stubbed with the minimal constructors and methods used when available, while
  still allowing the runtime guards to fall back when the packages are absent.
- For `fastmcp` we asked whether the orchestration server and handshake tests
  need more than the decorator, async context manager, and ``call_tool`` hook.
  Inspecting ``mcp_interface.create_server`` and the handshake fixture shows
  those members cover runtime usage, so the stub models them directly and keeps
  ``__getattr__`` available for the orchestrator handle.
  【F:src/autoresearch/mcp_interface.py†L8-L53】【F:tests/unit/test_a2a_mcp_handshake.py†L1-L36】【F:typings/fastmcp/__init__.pyi†L1-L38】
- `dspy` availability checks only assert the module imports and exposes a
  ``__version__`` attribute. The shim provides that constant and funnels other
  lookups through ``__getattr__`` so strict mode stays happy while real installs
  continue to expose the richer API.
  【F:src/autoresearch/search/context.py†L130-L163】【F:tests/targeted/test_extras_install.py†L70-L84】【F:typings/dspy/__init__.pyi†L1-L9】
- Streamlit knowledge-graph exports call ``PIL.Image.open`` on in-memory
  buffers, and the UI extras smoke test now exercises the loader. The stub keeps
  the module layout and exposes ``Image``, ``open``, and ``new`` so strict mode
  understands the minimal surface we rely on.
  【F:src/autoresearch/streamlit_app.py†L25-L37】【F:src/autoresearch/streamlit_app.py†L1736-L1754】【F:tests/targeted/test_extras_install.py†L70-L84】【F:typings/PIL/Image.pyi†L1-L20】

## Targeted strict checks

Running ``mypy --strict`` with ``MYPYPATH=tests/stubs`` on modules previously
blocked by third-party imports now succeeds when intrinsic issues are absent.
For example, `agents.feedback`—which only depended on `pydantic`—passes under
strict mode once its dictionary type annotation was tightened.【64b61d†L1-L2】
Modules such as `api.middleware` still report pre-existing missing annotations,
indicating the remaining work is unrelated to third-party typing gaps.
