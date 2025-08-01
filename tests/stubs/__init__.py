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
from . import git  # noqa: F401
from . import kuzu  # noqa: F401
from . import matplotlib  # noqa: F401
from . import pdfminer  # noqa: F401
from . import pil  # noqa: F401
from . import ray  # noqa: F401
from . import sentence_transformers  # noqa: F401
from . import slowapi  # noqa: F401
from . import spacy  # noqa: F401
from . import streamlit  # noqa: F401
from . import torch  # noqa: F401
from . import transformers  # noqa: F401
