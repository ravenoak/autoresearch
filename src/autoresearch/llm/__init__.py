from .registry import LLMFactory, get_llm_adapter
from .adapters import LLMAdapter, DummyAdapter, LMStudioAdapter, OpenAIAdapter

# Register default backends
LLMFactory.register("dummy", DummyAdapter)
LLMFactory.register("lmstudio", LMStudioAdapter)
LLMFactory.register("openai", OpenAIAdapter)

__all__ = [
    "LLMAdapter",
    "LLMFactory",
    "get_llm_adapter",
    "DummyAdapter",
    "LMStudioAdapter",
    "OpenAIAdapter",
]
