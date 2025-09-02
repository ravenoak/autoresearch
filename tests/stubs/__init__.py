"""Lightweight stubs for optional dependencies used in tests.

Importing this package installs stub modules into ``sys.modules`` so the
application can be imported without the real dependencies installed.
"""

# Import stub modules for their side effects.  Each module registers a stub
# implementation in ``sys.modules`` when imported.
from . import a2a  # noqa: F401
from . import bertopic  # noqa: F401
from . import docx  # noqa: F401
from . import duckdb  # noqa: F401
from . import fastmcp  # noqa: F401
from . import kuzu  # noqa: F401
from . import matplotlib  # noqa: F401
from . import pdfminer  # noqa: F401
from . import pil  # noqa: F401
from . import ray  # noqa: F401
from . import fastembed  # noqa: F401
from . import slowapi  # noqa: F401
from . import spacy  # noqa: F401
from . import streamlit  # noqa: F401
from . import torch  # noqa: F401
from . import dspy  # noqa: F401
from . import watchfiles  # noqa: F401
from . import networkx  # noqa: F401
from . import rdflib  # noqa: F401
from . import structlog  # noqa: F401
from . import loguru  # noqa: F401
from . import prometheus_client  # noqa: F401
from . import opentelemetry  # noqa: F401
from . import numpy  # noqa: F401
from . import tinydb  # noqa: F401
from . import limits  # noqa: F401
