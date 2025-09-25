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

## Targeted strict checks

Running ``mypy --strict`` with ``MYPYPATH=tests/stubs`` on modules previously
blocked by third-party imports now succeeds when intrinsic issues are absent.
For example, `agents.feedback`—which only depended on `pydantic`—passes under
strict mode once its dictionary type annotation was tightened.【64b61d†L1-L2】
Modules such as `api.middleware` still report pre-existing missing annotations,
indicating the remaining work is unrelated to third-party typing gaps.
