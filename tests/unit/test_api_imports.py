import inspect
import pytest
import importlib
import sys
from types import ModuleType

def test_no_unused_imports():
    """Test that api.py doesn't have unused imports."""
    # Import the module
    import autoresearch.api as api_module
    
    # Get all imported names
    imported_names = set()
    for name, obj in api_module.__dict__.items():
        if not name.startswith('_'):  # Skip private/special attributes
            imported_names.add(name)
    
    # Get all names used in the module's code
    module_code = inspect.getsource(api_module)
    
    # Check that OrchestrationError is not imported or is used
    assert 'OrchestrationError' not in imported_names or 'OrchestrationError' in module_code.replace('from .orchestration.orchestrator import Orchestrator, OrchestrationError', ''), \
        "OrchestrationError is imported but not used in api.py"