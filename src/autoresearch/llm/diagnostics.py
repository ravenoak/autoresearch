"""Context size diagnostics and reporting."""

from typing import Dict, Any
import logging

from ..llm.registry import get_available_adapters
from ..llm.context_management import get_context_manager
from ..llm.token_counting import is_tiktoken_available
from ..config import get_config
from ..logging_utils import get_logger

logger = get_logger(__name__)


def diagnose_context_capabilities() -> Dict[str, Any]:
    """Diagnose context capabilities across all adapters."""
    config = get_config()
    context_mgr = get_context_manager()

    report: Dict[str, Any] = {
        "providers": {},
        "tiktoken_available": False,
        "recommendations": []
    }

    # Check tiktoken availability
    report["tiktoken_available"] = is_tiktoken_available()
    if not report["tiktoken_available"]:
        report["recommendations"].append(
            "Install tiktoken for accurate token counting: pip install tiktoken"
        )

    # Get info from each adapter
    adapters = get_available_adapters()
    for provider_name, adapter_cls in adapters.items():
        try:
            adapter = adapter_cls()

            provider_info = {
                "models": [],
                "available": True
            }

            # Get available models
            models = adapter.available_models
            for model in models:
                context_size = context_mgr.get_context_size(model)
                model_info = {
                    "name": model,
                    "context_size": context_size,
                    "context_mb": round(context_size * 4 / 1024, 1)  # Rough estimate
                }
                provider_info["models"].append(model_info)

            report["providers"][provider_name] = provider_info

        except Exception as e:
            logger.debug(f"Could not diagnose {provider_name}: {e}")
            report["providers"][provider_name] = {
                "available": False,
                "error": str(e)
            }

    # Generate recommendations
    if not report["tiktoken_available"] and "openai" in report["providers"]:
        report["recommendations"].append(
            "tiktoken recommended for OpenAI models for 99%+ token accuracy"
        )

    # Check for small context models
    for provider, info in report["providers"].items():
        if info.get("available"):
            small_models = [m for m in info["models"] if m["context_size"] < 8192]
            if small_models:
                report["recommendations"].append(
                    f"{provider}: {len(small_models)} model(s) with <8k context. "
                    "Consider using models with larger context for complex queries."
                )

    return report


def print_context_report(report: Dict[str, Any]) -> None:
    """Print context diagnostics report."""
    print("\n=== Context Size Diagnostics ===\n")

    print(f"Accurate Token Counting: {'✓ Available' if report['tiktoken_available'] else '✗ Unavailable'}")
    print()

    for provider, info in report["providers"].items():
        if not info.get("available"):
            print(f"  {provider}: ✗ Unavailable ({info.get('error', 'unknown error')})")
            continue

        print(f"  {provider}: ✓ Available")
        for model in info["models"]:
            print(f"    - {model['name']}: {model['context_size']:,} tokens (~{model['context_mb']} MB)")
        print()

    if report["recommendations"]:
        print("Recommendations:")
        for i, rec in enumerate(report["recommendations"], 1):
            print(f"  {i}. {rec}")
        print()


def diagnose_context_metrics() -> Dict[str, Any]:
    """Get context-related metrics from the orchestration system."""
    from ..orchestration.metrics import OrchestrationMetrics

    metrics = OrchestrationMetrics()
    return metrics.get_context_stats()


def print_context_metrics_report(report: Dict[str, Any]) -> None:
    """Print context metrics report."""
    print("\n=== Context Metrics ===\n")

    # Utilization stats
    if report.get("utilization"):
        print("Context Utilization:")
        for model, stats in report["utilization"].items():
            print(f"  {model}: {stats['avg_percent']:.1f}% ({stats['avg_used']:,}/{stats['avg_available']:,} tokens)")
        print()

    # Truncation stats
    if report.get("truncations"):
        print("Truncation Events:")
        for model, stats in report["truncations"].items():
            print(f"  {model}: {stats['count']} events, {stats['avg_reduction_percent']:.1f}% reduction")
        print()

    # Chunking stats
    if report.get("chunking"):
        print("Chunking Operations:")
        for model, stats in report["chunking"].items():
            print(f"  {model}: {stats['count']} operations, avg {stats['avg_chunks']:.1f} chunks")
        print()

    # Error stats
    if report.get("errors"):
        print("Context Errors:")
        for model, stats in report["errors"].items():
            print(f"  {model}: {stats['total']} errors, {stats['recovery_rate']:.1f}% recovery rate")
        print()


def diagnose_context_full() -> None:
    """Run complete context diagnostics."""
    capabilities = diagnose_context_capabilities()
    print_context_report(capabilities)

    metrics = diagnose_context_metrics()
    print_context_metrics_report(metrics)
