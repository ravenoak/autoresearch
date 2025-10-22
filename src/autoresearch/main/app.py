from __future__ import annotations

# CLI entry point for Autoresearch with adaptive output formatting.

import importlib
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, List, Mapping, Optional, TypeVar, cast

import click
import typer

from ..cli_helpers import (
    depth_help_text,
    depth_option_callback,
    handle_command_not_found,
    format_scholarly_metadata,
    parse_agent_groups,
    render_scholarly_results,
)
from ..cli_utils import (
    Verbosity,
    VisualizationHooks,
    attach_cli_hooks,
    format_success,
    get_console,
    get_verbosity,
    print_command_example,
    print_error,
    print_info,
    print_success,
    print_verbose,
    print_warning,
    render_status_panel,
    set_bare_mode,
    set_verbosity,
    sparql_query_cli as _cli_sparql,
    visualize_metrics_cli,
    visualize_query_cli as _cli_visualize_query,
    visualize_rdf_cli as _cli_visualize,
)
from ..config.loader import ConfigLoader
from ..error_utils import format_error_for_cli, get_error_info
from ..errors import CitationError, NotFoundError, StorageError
from ..logging_utils import configure_logging
from ..mcp_interface import create_server
from ..monitor import monitor_app
from ..models import QueryResponse
from ..orchestration.reverify import ReverifyOptions, run_reverification
from ..output_format import OutputDepth

# Import StorageManager early so it's available for tests
from ..storage import StorageManager, WorkspaceManifest
from ..resources.scholarly import ScholarlyService

# Make _config_loader available for tests (will be set after _config_loader is defined)


app = cast(
    typer.Typer,
    cast(Any, typer).Typer(
        help=(
            "Autoresearch CLI entry point.\n\n"
            "Set the reasoning mode using --mode or in autoresearch.toml under "
            "[core.reasoning_mode]. Valid values: auto, direct, dialectical, "
            "chain-of-thought. Use --primus-start to choose the starting agent "
            "for dialectical reasoning."
        ),
        name="autoresearch",
        no_args_is_help=True,  # Show help when no arguments are provided
        pretty_exceptions_enable=False,
        # Disable pretty exceptions to handle them ourselves
    ),
)

scholarly_service = ScholarlyService()

F = TypeVar("F", bound=Callable[..., Any])


def _dispatch_gui_event(event: str, payload: Optional[Mapping[str, Any]] = None) -> None:
    """Best-effort forwarding of legacy GUI telemetry events."""

    try:
        analytics_module = importlib.import_module("autoresearch.analytics")
    except Exception:  # pragma: no cover - analytics optional in tests
        return

    dispatch = getattr(analytics_module, "dispatch_event", None)
    if not callable(dispatch):
        return

    try:
        dispatch(event, dict(payload or {}))
    except Exception:  # pragma: no cover - defensive guard
        logging.getLogger(__name__).debug(
            "Failed to dispatch GUI analytics event '%s'", event, exc_info=True
        )


def typed_callback(**kwargs: Any) -> Callable[[F], F]:
    """Return a type-preserving Typer callback decorator."""

    return cast("Callable[[F], F]", app.callback(**kwargs))


def typed_command(*args: Any, **kwargs: Any) -> Callable[[F], F]:
    """Return a type-preserving Typer command decorator."""

    return cast("Callable[[F], F]", app.command(*args, **kwargs))


# Provide test hooks without mutating private Typer attributes directly.
visualization_hooks: VisualizationHooks = attach_cli_hooks(
    app,
    visualize=_cli_visualize,
    visualize_query=_cli_visualize_query,
    name="autoresearch",
)
# Expose a patchable orchestrator handle for tests, defaulting to the real class
try:
    _orchestrator_module = importlib.import_module("autoresearch.orchestration.orchestrator")
except Exception:  # pragma: no cover - fallback for environments without extras
    Orchestrator: Any | None = None
else:
    Orchestrator = getattr(_orchestrator_module, "Orchestrator", None)
try:
    _workspace_module = importlib.import_module("autoresearch.orchestration.workspace")
except Exception:  # pragma: no cover - fallback when extras missing
    WorkspaceOrchestrator: Any | None = None
else:
    WorkspaceOrchestrator = getattr(_workspace_module, "WorkspaceOrchestrator", None)
_config_loader: ConfigLoader = ConfigLoader()


from ..cli_backup import backup_app as _backup_app  # noqa: E402
from ..cli_evaluation import evaluation_app as _evaluation_app  # noqa: E402

from .config_cli import config_app as _config_app, config_init  # noqa: E402  # isort: skip

config_app: typer.Typer = _config_app
app.add_typer(config_app, name="config")

backup_app = _backup_app
app.add_typer(backup_app, name="backup")

evaluation_app = _evaluation_app
app.add_typer(evaluation_app, name="evaluate")


workspace_app = cast(
    typer.Typer,
    cast(Any, typer).Typer(
        help=(
            "Manage workspace manifests and trigger debates scoped to curated resources."
        ),
        pretty_exceptions_enable=False,
    ),
)
app.add_typer(workspace_app, name="workspace")

workspace_papers_app = cast(
    typer.Typer,
    cast(Any, typer).Typer(
        help="Search and cache scholarly papers for workspaces.",
        pretty_exceptions_enable=False,
    ),
)
workspace_app.add_typer(workspace_papers_app, name="papers")


def _parse_workspace_resource_option(entry: str) -> dict[str, Any]:
    """Parse resource definitions encoded as ``kind:reference[?optional]``."""

    if ":" not in entry:
        raise typer.BadParameter("Resources must use the format KIND:REFERENCE")
    kind, reference = entry.split(":", 1)
    kind = kind.strip().lower()
    reference_value, _, flag_token = reference.partition("?")
    reference_value = reference_value.strip()
    citation_required = True
    if flag_token:
        flag_normalized = flag_token.strip().lower()
        if flag_normalized in {"optional", "opt"}:
            citation_required = False
        else:
            raise typer.BadParameter(
                "Unknown workspace resource flag. Use '?optional' to disable required citations."
            )
    if not kind or not reference_value:
        raise typer.BadParameter("Resource kind and reference cannot be empty")
    return {
        "kind": kind,
        "reference": reference_value,
        "citation_required": citation_required,
    }


def _render_manifest_summary(manifest: WorkspaceManifest) -> None:
    console = get_console()
    console.print(format_success(f"Workspace '{manifest.name}' (v{manifest.version})"))
    for resource in manifest.resources:
        flag = "required" if resource.citation_required else "optional"
        console.print(f"- [{flag}] {resource.kind}: {resource.reference}")


def workspace_command(*args: Any, **kwargs: Any) -> Callable[[F], F]:
    """Return a type-preserving decorator for workspace subcommands."""

    return cast("Callable[[F], F]", workspace_app.command(*args, **kwargs))


@workspace_command("create")
def workspace_create(
    name: str = typer.Argument(..., help="Human readable workspace name."),
    resource: List[str] = typer.Option(
        ...,  # noqa: B008
        "--resource",
        "-r",
        help="Resource descriptor KIND:REFERENCE. Append '?optional' to allow missing citations.",
    ),
    slug: Optional[str] = typer.Option(
        None,
        "--slug",
        help="Optional workspace identifier slug overriding the derived value.",
    ),
) -> None:
    """Create or version a workspace manifest."""

    StorageManager.setup()
    if not resource:
        raise typer.BadParameter("Provide at least one --resource entry", param_hint="--resource")
    payload = [_parse_workspace_resource_option(entry) for entry in resource]
    manifest_payload: dict[str, Any] = {"name": name, "resources": payload}
    if slug:
        manifest_payload["workspace_id"] = slug
    manifest = StorageManager.save_workspace_manifest(manifest_payload, increment_version=True)
    _render_manifest_summary(manifest)


@workspace_command("select")
def workspace_select(
    workspace: str = typer.Argument(..., help="Workspace slug to inspect."),
    version: Optional[int] = typer.Option(None, "--version", help="Manifest version number."),
    manifest_id: Optional[str] = typer.Option(None, "--manifest-id", help="Specific manifest identifier."),
) -> None:
    """Display workspace manifest details."""

    StorageManager.setup()
    try:
        manifest = StorageManager.get_workspace_manifest(workspace, version=version, manifest_id=manifest_id)
    except Exception as exc:
        print_error(f"Failed to load workspace '{workspace}': {exc}")
        raise typer.Exit(1) from exc
    _render_manifest_summary(manifest)


@workspace_command("debate")
def workspace_debate(
    workspace: str = typer.Argument(..., help="Workspace slug to scope the debate."),
    prompt: str = typer.Argument(..., help="Prompt to investigate."),
    version: Optional[int] = typer.Option(None, "--version", help="Manifest version override."),
    manifest_id: Optional[str] = typer.Option(None, "--manifest-id", help="Manifest identifier override."),
) -> None:
    """Run a dialectical debate constrained by workspace resources."""

    StorageManager.setup()
    config = _config_loader.config
    orchestrator_instance: Any
    if WorkspaceOrchestrator is not None:
        orchestrator_instance = WorkspaceOrchestrator()
        run_kwargs = {
            "workspace_id": workspace,
            "manifest_version": version,
            "manifest_id": manifest_id,
        }
        try:
            result = orchestrator_instance.run_query(
                prompt,
                config,
                None,
                **run_kwargs,
            )
        except CitationError as exc:
            print_error(f"Citation requirements not met: {exc}")
            raise typer.Exit(1) from exc
    elif Orchestrator is not None:
        orchestrator_instance = Orchestrator()
        print_warning(
            "WorkspaceOrchestrator unavailable; running debate without citation enforcement."
        )
        result = orchestrator_instance.run_query(prompt, config)
    else:  # pragma: no cover - defensive fallback
        print_error("No orchestrator available in this environment")
        raise typer.Exit(1)

    if not isinstance(result, QueryResponse):
        print_info("Debate completed but returned unexpected payload")
        return

    console = get_console()
    console.print(format_success("Debate completed"))
    console.print(result.answer)


@workspace_papers_app.command("search")
def workspace_papers_search(
    query: str = typer.Argument(..., help="Query string to search across scholarly providers."),
    limit: int = typer.Option(5, "--limit", "-n", help="Maximum results per provider."),
    provider: list[str] = typer.Option(
        [],
        "--provider",
        "-p",
        help="Restrict search to specific providers (e.g. arxiv, huggingface).",
    ),
) -> None:
    """Search scholarly providers for papers."""

    try:
        results = scholarly_service.search(query, providers=provider or None, limit=limit)
    except Exception as exc:  # pragma: no cover - defensive
        print_error(f"Scholarly search failed: {exc}")
        raise typer.Exit(1) from exc
    render_scholarly_results(results)


@workspace_papers_app.command("list")
def workspace_papers_list(
    workspace: Optional[str] = typer.Option(
        None,
        "--workspace",
        "-w",
        help="Workspace slug to infer namespace. Defaults to global namespace.",
    ),
    provider: Optional[str] = typer.Option(None, "--provider", "-p", help="Filter by provider."),
) -> None:
    """List cached scholarly papers."""

    try:
        cached = scholarly_service.list_cached(namespace=workspace, provider=provider)
    except Exception as exc:  # pragma: no cover - defensive
        print_error(f"Failed to list cached papers: {exc}")
        raise typer.Exit(1) from exc
    if not cached:
        print_info("No cached papers found.")
        return
    for item in cached:
        print_info(format_scholarly_metadata(item.metadata), symbol=False)
        print_info(f"  Cache: {item.cache_path}", symbol=False)
        print_info(f"  Namespace: {item.metadata.identifier.namespace}", symbol=False)


@workspace_papers_app.command("ingest")
def workspace_papers_ingest(
    provider: str = typer.Argument(..., help="Provider identifier (arxiv, huggingface)."),
    identifier: str = typer.Argument(..., help="Provider-specific paper identifier."),
    workspace: Optional[str] = typer.Option(
        None,
        "--workspace",
        "-w",
        help="Workspace slug to attach the cache and default namespace.",
    ),
    namespace: Optional[str] = typer.Option(
        None,
        "--namespace",
        help="Explicit namespace override for caching.",
    ),
    attach: bool = typer.Option(
        False,
        "--attach/--no-attach",
        help="Attach the cached paper to the workspace manifest after ingestion.",
    ),
) -> None:
    """Fetch and cache a scholarly paper."""

    StorageManager.setup()
    default_namespace, _, _ = StorageManager._namespace_settings()
    target_namespace = namespace or workspace or default_namespace
    try:
        cached = scholarly_service.ingest(
            provider,
            identifier,
            namespace=target_namespace,
        )
    except Exception as exc:  # pragma: no cover - defensive
        print_error(f"Failed to ingest paper: {exc}")
        raise typer.Exit(1) from exc
    print_info("Cached paper:")
    print_info(format_scholarly_metadata(cached.metadata), symbol=False)
    print_info(f"Stored at {cached.cache_path}", symbol=False)
    if attach and workspace:
        _attach_cached_paper_to_workspace(workspace, cached)


@workspace_papers_app.command("attach")
def workspace_papers_attach(
    workspace: str = typer.Argument(..., help="Workspace slug to update."),
    provider: str = typer.Argument(..., help="Provider identifier for the cached paper."),
    paper_id: str = typer.Argument(..., help="Paper identifier scoped to the provider."),
    citation_required: bool = typer.Option(
        True,
        "--citation-required/--optional",
        help="Mark citations from this resource as required.",
    ),
) -> None:
    """Attach an existing cached paper to a workspace manifest."""

    StorageManager.setup()
    try:
        payload = StorageManager.get_scholarly_paper(workspace, provider, paper_id)
    except NotFoundError as exc:
        print_error(f"Cached paper not found: {exc}")
        raise typer.Exit(1) from exc
    metadata = payload.get("metadata", {})
    resource_payload = {
        "kind": "paper",
        "reference": f"{provider}:{paper_id}",
        "citation_required": citation_required,
        "metadata": {
            "title": metadata.get("title"),
            "cache_path": payload.get("cache_path"),
            "primary_url": metadata.get("primary_url"),
            "provenance": payload.get("provenance"),
        },
    }
    try:
        manifest = StorageManager.get_workspace_manifest(workspace)
    except NotFoundError as exc:
        print_error(f"Workspace '{workspace}' does not exist: {exc}")
        raise typer.Exit(1) from exc
    resources = [resource.to_payload() for resource in manifest.resources]
    resources.append(resource_payload)
    new_manifest = StorageManager.save_workspace_manifest(
        {
            "workspace_id": manifest.workspace_id,
            "name": manifest.name,
            "resources": resources,
        }
    )
    print_info(f"Workspace '{workspace}' updated to version {new_manifest.version}.")


def _attach_cached_paper_to_workspace(workspace: str, cached: Any) -> None:
    """Append ``cached`` to ``workspace`` manifest."""

    try:
        manifest = StorageManager.get_workspace_manifest(workspace)
    except NotFoundError as exc:
        print_error(f"Workspace '{workspace}' does not exist: {exc}")
        raise typer.Exit(1) from exc
    resource_payload = {
        "kind": "paper",
        "reference": f"{cached.metadata.identifier.provider}:{cached.metadata.primary_key()}",
        "citation_required": True,
        "metadata": {
            "title": cached.metadata.title,
            "cache_path": str(cached.cache_path),
            "primary_url": cached.metadata.primary_url,
            "provenance": cached.provenance.to_payload(),
        },
    }
    resources = [resource.to_payload() for resource in manifest.resources]
    resources.append(resource_payload)
    StorageManager.save_workspace_manifest(
        {
            "workspace_id": manifest.workspace_id,
            "name": manifest.name,
            "resources": resources,
        }
    )
    print_info(f"Attached paper to workspace '{workspace}' (new version pending).")


@typed_callback(invoke_without_command=False)
def start_watcher(
    ctx: click.Context,
    vss_path: Optional[str] = typer.Option(
        None,
        "--vss-path",
        help=("Path to VSS extension file. Overrides config and environment settings."),
    ),
    no_vss: bool = typer.Option(
        False,
        "--no-vss",
        help="Disable VSS extension loading even if enabled in config.",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose output with detailed information.",
    ),
    quiet: bool = typer.Option(
        False,
        "--quiet",
        "-q",
        help="Suppress all non-essential output.",
    ),
    log_format: Optional[str] = typer.Option(
        None,
        "--log-format",
        help="Log output format: json, console, or auto (default: auto).",
    ),
    quiet_logs: bool = typer.Option(
        False,
        "--quiet-logs",
        help="Suppress diagnostic log messages, showing only errors and warnings.",
    ),
    bare_mode: bool = typer.Option(
        False,
        "--bare-mode",
        help="Disable colors, symbols, and decorative formatting for plain text output.",
    ),
    show_sections: bool = typer.Option(
        False,
        "--show-sections",
        help="Display available sections for the selected depth level.",
    ),
    include_sections: Optional[str] = typer.Option(
        None,
        "--include",
        help="Comma-separated list of sections to include (e.g., 'metrics,reasoning').",
    ),
    exclude_sections: Optional[str] = typer.Option(
        None,
        "--exclude",
        help="Comma-separated list of sections to exclude (e.g., 'raw_response,citations').",
    ),
    reset_sections: bool = typer.Option(
        False,
        "--reset-sections",
        help="Reset all section customizations to depth defaults.",
    ),
) -> None:
    """Start configuration watcher before executing commands."""
    # Set verbosity level based on command line options
    if verbose and quiet:
        print_warning("Both --verbose and --quiet specified. Using --verbose.")
        set_verbosity(Verbosity.VERBOSE)
    elif verbose:
        set_verbosity(Verbosity.VERBOSE)
        print_verbose("Verbose mode enabled")
    elif quiet:
        set_verbosity(Verbosity.QUIET)
    else:
        set_verbosity(Verbosity.NORMAL)
    # When help is requested, avoid initializing runtime dependencies.
    # ``ctx.resilient_parsing`` is ``True`` in Click when ``--help`` or ``-h`` is
    # present on the command line, including during Typer's ``CliRunner`` tests.
    if getattr(ctx, "resilient_parsing", False):
        os.environ["COLUMNS"] = "200"
        return
    # Set environment variables for VSS extension control if CLI options are provided
    if no_vss:
        os.environ["VECTOR_EXTENSION"] = "false"
    if vss_path:
        os.environ["VECTOR_EXTENSION_PATH"] = vss_path

    # If help is requested anywhere on the command line, skip prompts and initialization
    cli_args = tuple(getattr(ctx, "args", ()) or ())
    if any(arg in {"--help", "-h"} for arg in cli_args) or any(
        arg in {"--help", "-h"} for arg in sys.argv
    ):
        # Ensure wide help to avoid truncation of long option names in tests
        os.environ["COLUMNS"] = "200"
        return

    console = get_console()

    # Check if this is the first run by looking for config files
    is_first_run = True
    for path in _config_loader.search_paths:
        if path.exists():
            is_first_run = False
            break

    # Show welcome message on first run
    invoked_subcommand = getattr(ctx, "invoked_subcommand", None)
    if is_first_run and invoked_subcommand is None:
        console.print("\n" + format_success("Welcome to Autoresearch!", symbol=False))
        console.print(
            "A local-first research assistant that coordinates multiple agents "
            "to produce evidence-backed answers.\n"
        )

        print_info("Getting Started:", symbol=False)
        console.print("1. Initialize configuration:")
        print_command_example("autoresearch config init")
        console.print("2. Run a search query:")
        print_command_example('autoresearch search "Your question here"')
        console.print("3. Start interactive mode:")
        print_command_example("autoresearch monitor")
        console.print("")

        print_info("Available Commands:", symbol=False)
        print_command_example("search", "Run a search query")
        print_command_example("monitor", "Start interactive resource and metrics monitor")
        print_command_example("config", "Configuration management commands")
        print_command_example("backup", "Backup and restore operations")
        print_command_example("serve", "Start an MCP server")
        print_command_example("serve_a2a", "Start an A2A server")
        console.print("")

        print_command_example("autoresearch --help", "Show detailed help information")
        console.print("")

        # Suggest initializing configuration
        if typer.confirm("Would you like to initialize the configuration now?", default=True):
            ctx.invoke(config_init)
            return

    # Configure logging with CLI options
    from ..logging_utils import LoggingConfig

    # Start with environment-based config
    config = LoggingConfig.from_env()

    # Override with CLI options if provided
    if log_format is not None:
        if log_format not in ("json", "console", "auto"):
            print_error(f"Invalid log format: {log_format}. Valid options: json, console, auto")
            raise typer.Exit(code=1)
        config.format = log_format  # type: ignore

    # Configure quiet logs by setting log level
    if quiet_logs:
        config.level = logging.WARNING  # Show only warnings and errors

    # Set bare mode environment variable for CLI utilities
    set_bare_mode(bare_mode)
    console = get_console()

    configure_logging(config)

    # After CLI options are parsed, reconfigure logging if needed
    # This ensures environment variables set by CLI options take effect
    if log_format is not None or quiet_logs or bare_mode:
        # Reconfigure with the final settings
        final_config = LoggingConfig.from_env()
        configure_logging(final_config)

    # Skip heavy initialization when help is requested to ensure `--help` always works
    if any(arg in {"--help", "-h"} for arg in sys.argv):
        return

    watch_ctx = _config_loader.watching()
    watch_ctx.__enter__()

    def _stop_watcher() -> None:
        try:
            watch_ctx.__exit__(None, None, None)
        finally:
            _config_loader.stop_watching()

    call_on_close = getattr(ctx, "call_on_close", None)
    if callable(call_on_close):
        call_on_close(_stop_watcher)


@typed_command()
def search(
    query: str = typer.Argument(..., help="Natural-language query to process"),
    output: Optional[str] = typer.Option(
        None, "-o", "--output", help="Output format: json|markdown|plain"
    ),
    depth: Optional[str] = typer.Option(
        None,
        "--depth",
        help=f"Depth of detail in CLI output ({depth_help_text()})",
        callback=depth_option_callback,
    ),
    interactive: bool = typer.Option(
        False,
        "--interactive",
        "-i",
        help="Refine the query interactively between agent cycles",
    ),
    reasoning_mode: Optional[str] = typer.Option(
        None,
        "--reasoning-mode",
        "--mode",
        help=(
            "Override reasoning mode for this run " "(auto, direct, dialectical, chain-of-thought)"
        ),
    ),
    loops: Optional[int] = typer.Option(
        None,
        "--loops",
        help="Number of reasoning cycles to run",
    ),
    ontology: Optional[str] = typer.Option(
        None,
        "--ontology",
        help="Load an ontology file before executing the query",
    ),
    ontology_reasoner: Optional[str] = typer.Option(
        None,
        "--ontology-reasoner",
        "--reasoner",
        help="Ontology reasoner engine to apply",
    ),
    ontology_reasoning: bool = typer.Option(
        False,
        "--ontology-reasoning/--no-ontology-reasoning",
        "--infer-relations",
        help="Apply ontology reasoning before returning results",
    ),
    token_budget: Optional[int] = typer.Option(
        None,
        "--token-budget",
        help="Maximum tokens available for this query",
    ),
    gate_policy_enabled: Optional[bool] = typer.Option(
        None,
        "--gate-policy-enabled",
        help="Enable scout gate heuristics (true/false).",
        show_default=False,
    ),
    gate_retrieval_overlap_threshold: Optional[float] = typer.Option(
        None,
        "--gate-overlap-threshold",
        help="Minimum retrieval overlap that still triggers debate (0-1).",
        show_default=False,
    ),
    gate_nli_conflict_threshold: Optional[float] = typer.Option(
        None,
        "--gate-conflict-threshold",
        help="Contradiction probability threshold for debate escalation (0-1).",
        show_default=False,
    ),
    gate_complexity_threshold: Optional[float] = typer.Option(
        None,
        "--gate-complexity-threshold",
        help="Complexity score threshold for debate escalation (0-1).",
        show_default=False,
    ),
    gate_user_overrides: Optional[str] = typer.Option(
        None,
        "--gate-overrides",
        help='JSON overrides for the scout gate policy (e.g. \'{"decision": "force_exit"}\').',
        show_default=False,
    ),
    adaptive_max_factor: Optional[int] = typer.Option(
        None,
        "--adaptive-max-factor",
        help="Adaptive budgeting max multiplier for query tokens",
    ),
    adaptive_min_buffer: Optional[int] = typer.Option(
        None,
        "--adaptive-min-buffer",
        help="Adaptive budgeting minimum extra tokens",
    ),
    circuit_breaker_threshold: Optional[int] = typer.Option(
        None,
        "--circuit-breaker-threshold",
        help="Failures before an agent circuit opens",
    ),
    circuit_breaker_cooldown: Optional[int] = typer.Option(
        None,
        "--circuit-breaker-cooldown",
        help="Circuit breaker cooldown period in seconds",
    ),
    agents: Optional[str] = typer.Option(
        None,
        "--agents",
        help="Comma-separated list of agents to run",
    ),
    parallel: bool = typer.Option(
        False,
        "--parallel",
        help="Run agent groups in parallel",
    ),
    agent_groups: Optional[str] = typer.Option(
        None,
        "--agent-groups",
        help=(
            "Agent groups to run in parallel. Provide a comma-separated list of agents. "
            "Multiple groups can be separated by repeating the option when supported."
        ),
    ),
    primus_start: Optional[int] = typer.Option(
        None,
        "--primus-start",
        help="Index of the agent to begin the dialectical cycle",
    ),
    visualize: bool = typer.Option(
        False,
        "--visualize",
        help="Render an inline knowledge graph after the query completes",
    ),
    tui: bool = typer.Option(
        False,
        "--tui",
        help=(
            "Display an interactive Textual dashboard while the query runs "
            "(requires a TTY and Textual; see docs/tui_dashboard.md)."
        ),
    ),
    graphml: Optional[Path] = typer.Option(
        None,
        "--graphml",
        help="Write the knowledge graph as GraphML to this path (use '-' for stdout).",
    ),
    graph_json: Optional[Path] = typer.Option(
        None,
        "--graph-json",
        help="Write the knowledge graph as Graph JSON to this path (use '-' for stdout).",
    ),
    show_sections: bool = typer.Option(
        False,
        "--show-sections",
        help="Display available sections for the selected depth level.",
    ),
    include_sections: Optional[str] = typer.Option(
        None,
        "--include",
        help="Comma-separated list of sections to include (e.g., 'metrics,reasoning').",
    ),
    exclude_sections: Optional[str] = typer.Option(
        None,
        "--exclude",
        help="Comma-separated list of sections to exclude (e.g., 'raw_response,citations').",
    ),
    reset_sections: bool = typer.Option(
        False,
        "--reset-sections",
        help="Reset all section customizations to depth defaults.",
    ),
) -> None:
    """Run a search query through the orchestrator and format the result.

    This command processes a natural language query through the orchestrator,
    which coordinates multiple agents to produce an evidence-backed answer.

    Examples:
        # Basic query
        autoresearch search "What is quantum computing?"

        # Query with JSON output format
        autoresearch search "What is the capital of France?" --output json

        # Query with plain text output format
        autoresearch search "Who was Albert Einstein?" -o plain

        # Display a simple knowledge graph in the terminal
        autoresearch search "What is quantum computing?" --visualize

        # Watch query progress in the Textual dashboard
        autoresearch search --tui "What is quantum computing?"

        # Export knowledge graph artifacts for offline analysis
        autoresearch search "Explain AI ethics" --graphml graph.graphml --graph-json graph.json

        # Limit tokens and run multiple loops
        autoresearch search --loops 3 --token-budget 2000 "Explain AI ethics"

        # Adjust circuit breaker thresholds
        autoresearch search "Test" --circuit-breaker-threshold 5 --circuit-breaker-cooldown 60

        # Tune adaptive token budgeting
        autoresearch search "Long query" --adaptive-max-factor 25 --adaptive-min-buffer 20

        # Choose specific agents
        autoresearch search --agents Synthesizer,Contrarian "What is quantum computing?"

        # Run agent groups in parallel
        autoresearch search --parallel --agent-groups "Synthesizer,Contrarian" \
            "FactChecker" "Impacts of AI"

        # Options overview (for reference)
        # --interactive, --loops, --ontology, --ontology-reasoner, --infer-relations, --visualize
    """
    config = _config_loader.load_config()

    # Lazy imports to avoid side effects during help rendering
    from ..output_format import OutputFormatter

    try:
        StorageManager.setup()
    except StorageError as e:
        # Fail fast when storage initialization fails to ensure clear feedback in CLI.
        # Use plain stdout to satisfy tests that assert on stdout content.
        print(f"Storage initialization failed: {e}")
        raise typer.Exit(code=1)

    # Resolve orchestrator: prefer module-level handle (for tests) else import
    OrchestratorLocal = Orchestrator
    if OrchestratorLocal is None:
        from ..orchestration.orchestrator import Orchestrator as _OrchestratorLocal

        OrchestratorLocal = _OrchestratorLocal
    if OrchestratorLocal is None:
        raise RuntimeError(
            "Autoresearch orchestrator is unavailable. Install optional extras to run queries.",
        )

    updates: dict[str, Any] = {}
    if reasoning_mode is not None:
        updates["reasoning_mode"] = reasoning_mode
    if loops is not None:
        updates["loops"] = loops
    if token_budget is not None:
        updates["token_budget"] = token_budget
    if adaptive_max_factor is not None:
        updates["adaptive_max_factor"] = adaptive_max_factor
    if adaptive_min_buffer is not None:
        updates["adaptive_min_buffer"] = adaptive_min_buffer
    if circuit_breaker_threshold is not None:
        updates["circuit_breaker_threshold"] = circuit_breaker_threshold
    if circuit_breaker_cooldown is not None:
        updates["circuit_breaker_cooldown"] = circuit_breaker_cooldown
    if gate_policy_enabled is not None:
        updates["gate_policy_enabled"] = gate_policy_enabled
    if gate_retrieval_overlap_threshold is not None:
        updates["gate_retrieval_overlap_threshold"] = gate_retrieval_overlap_threshold
    if gate_nli_conflict_threshold is not None:
        updates["gate_nli_conflict_threshold"] = gate_nli_conflict_threshold
    if gate_complexity_threshold is not None:
        updates["gate_complexity_threshold"] = gate_complexity_threshold
    if gate_user_overrides is not None:
        try:
            overrides = json.loads(gate_user_overrides)
        except json.JSONDecodeError as exc:
            print_error(
                "Invalid JSON for --gate-overrides. Provide a valid JSON object.",
                suggestion=str(exc),
            )
            raise typer.Exit(code=1) from exc
        updates["gate_user_overrides"] = overrides
    if primus_start is not None:
        updates["primus_start"] = primus_start
    if agents is not None:
        updates["agents"] = [a.strip() for a in agents.split(",") if a.strip()]
    storage_updates: dict[str, Any] = {}
    if ontology_reasoner is not None:
        storage_updates["ontology_reasoner"] = ontology_reasoner
    if storage_updates:
        updates["storage"] = config.storage.model_copy(update=storage_updates)
    if updates:
        config = config.model_copy(update=updates)

    if ontology:
        StorageManager.load_ontology(ontology)
    if ontology_reasoning and Orchestrator is not None:
        Orchestrator.infer_relations()

    # Check if query is empty or missing (this shouldn't happen with typer, but just in case)
    if not query or query.strip() == "":
        print_warning("You need to provide a query to search for.")
        print_command_example('autoresearch search "What is quantum computing?"', "Example query")
        print_command_example("autoresearch search --help", "Show help for search command")
        return

    try:
        loops = getattr(config, "loops", 1)

        def _run_serial_with_callbacks(
            callbacks: Mapping[str, Callable[..., Any]] | None = None,
        ) -> QueryResponse:
            callback_map = dict(callbacks or {})
            return OrchestratorLocal().run_query(
                query,
                config,
                callbacks=callback_map,
                visualize=visualize,
            )

        def _run_with_progress() -> QueryResponse:
            from . import Progress, Prompt

            def on_cycle_end(loop: int, state: Any) -> None:
                progress.update(task, advance=1)
                if interactive and loop < loops - 1:
                    refinement = Prompt.ask(
                        "Refine query or press Enter to continue (q to abort)",
                        default="",
                        validator=lambda value: value.strip(),
                    )
                    if refinement.lower() == "q":
                        state.error_count = getattr(config, "max_errors", 3)
                    elif refinement:
                        state.query = refinement

            with Progress() as progress:
                if parallel and agent_groups:
                    groups = parse_agent_groups([agent_groups])
                    task = progress.add_task(
                        "[green]Processing query...",
                        total=len(groups),
                    )
                    return OrchestratorLocal.run_parallel_query(query, config, groups)
                task = progress.add_task(
                    "[green]Processing query...",
                    total=loops,
                )
                return _run_serial_with_callbacks({"on_cycle_end": on_cycle_end})

        bare_mode_active = os.getenv("AUTORESEARCH_BARE_MODE", "false").lower() in {
            "true",
            "1",
            "yes",
            "on",
        }
        use_tui = False
        tui_block_reason: str | None = None
        if tui:
            if not sys.stdout.isatty():
                tui_block_reason = (
                    "Interactive dashboard requires a TTY; falling back to standard output."
                )
            elif bare_mode_active:
                tui_block_reason = (
                    "Bare mode disables the dashboard to preserve plain output; using legacy renderer."
                )
            elif interactive:
                tui_block_reason = (
                    "Interactive refinement is not supported inside the Textual dashboard; using standard output."
                )
            elif parallel or agent_groups:
                tui_block_reason = (
                    "The dashboard does not yet support parallel execution or custom agent groups;"
                    " using standard output."
                )
            else:
                use_tui = True
        if tui_block_reason:
            print_warning(tui_block_reason)

        try:
            if use_tui:
                from ..ui.tui import DashboardUnavailableError, run_dashboard

                try:
                    result = run_dashboard(
                        runner=_run_serial_with_callbacks,
                        total_loops=int(loops),
                        hooks=visualization_hooks,
                    )
                except DashboardUnavailableError as exc:
                    if exc.__cause__ is not None:
                        raise exc.__cause__ from exc
                    print_warning(str(exc))
                    result = _run_with_progress()
            else:
                result = _run_with_progress()
        except Exception as e:
            error_info = get_error_info(e)
            error_msg, suggestion, code_example = format_error_for_cli(error_info)
            print_error(
                f"Query processing failed: {error_msg}",
                suggestion=suggestion,
                code_example=code_example,
            )
            raise typer.Exit(code=1) from e

        fmt = output or (
            "markdown"
            if os.getenv("PYTEST_CURRENT_TEST")
            else ("json" if not sys.stdout.isatty() else "markdown")
        )

        # Handle section control options
        section_overrides = None
        if show_sections or include_sections or exclude_sections or reset_sections:
            from ..output_format import _SECTION_LABELS, describe_depth_features

            # Get the normalized depth
            normalized_depth = cast(Optional[OutputDepth], depth)

            if show_sections:
                # Show available sections for the selected depth
                if normalized_depth is None:
                    normalized_depth = OutputDepth.STANDARD

                features = describe_depth_features()
                depth_features = features.get(normalized_depth, {})

                print_info(f"Available sections for {normalized_depth.label} depth:")
                for section_key, included in depth_features.items():
                    status = "✓" if included else "✗"
                    section_name = _SECTION_LABELS.get(section_key, section_key)
                    print_info(f"  {status} {section_name} ({section_key})", symbol=False)

                # Don't process the query if only showing sections
                return

            # Parse include/exclude sections
            include_set = set()
            exclude_set = set()

            if include_sections:
                include_set = {s.strip() for s in include_sections.split(",") if s.strip()}

            if exclude_sections:
                exclude_set = {s.strip() for s in exclude_sections.split(",") if s.strip()}

            # Validate section names
            valid_sections = set(_SECTION_LABELS.keys())
            invalid_sections = (include_set | exclude_set) - valid_sections

            if invalid_sections:
                print_error(
                    f"Invalid section name(s): {', '.join(sorted(invalid_sections))}",
                    suggestion=f"Valid sections: {', '.join(sorted(valid_sections))}",
                )
                raise typer.Exit(code=1)

            # Create section overrides
            if include_set or exclude_set or reset_sections:
                from ..output_format import _DEPTH_PLANS

                base_plan = _DEPTH_PLANS.get(normalized_depth or OutputDepth.STANDARD)
                if base_plan is None:
                    raise typer.Exit(code=1)

                # Start with base plan settings
                section_overrides = {
                    "include_tldr": base_plan.include_tldr,
                    "include_key_findings": base_plan.include_key_findings,
                    "include_citations": base_plan.include_citations,
                    "include_claims": base_plan.include_claims,
                    "include_reasoning": base_plan.include_reasoning,
                    "include_metrics": base_plan.include_metrics,
                    "include_raw": base_plan.include_raw,
                    "include_task_graph": base_plan.include_task_graph,
                    "include_react_traces": base_plan.include_react_traces,
                    "include_knowledge_graph": base_plan.include_knowledge_graph,
                    "include_graph_exports": base_plan.include_graph_exports,
                }

                # Apply include overrides (force include)
                for section in include_set:
                    if section == "tldr":
                        section_overrides["include_tldr"] = True
                    elif section == "key_findings":
                        section_overrides["include_key_findings"] = True
                    elif section == "citations":
                        section_overrides["include_citations"] = True
                    elif section == "claim_audits":
                        section_overrides["include_claims"] = True
                    elif section == "reasoning":
                        section_overrides["include_reasoning"] = True
                    elif section == "metrics":
                        section_overrides["include_metrics"] = True
                    elif section == "raw_response":
                        section_overrides["include_raw"] = True
                    elif section == "task_graph":
                        section_overrides["include_task_graph"] = True
                    elif section == "react_traces":
                        section_overrides["include_react_traces"] = True
                    elif section == "knowledge_graph":
                        section_overrides["include_knowledge_graph"] = True
                    elif section == "graph_exports":
                        section_overrides["include_graph_exports"] = True

                # Apply exclude overrides (force exclude)
                for section in exclude_set:
                    if section == "tldr":
                        section_overrides["include_tldr"] = False
                    elif section == "key_findings":
                        section_overrides["include_key_findings"] = False
                    elif section == "citations":
                        section_overrides["include_citations"] = False
                    elif section == "claim_audits":
                        section_overrides["include_claims"] = False
                    elif section == "reasoning":
                        section_overrides["include_reasoning"] = False
                    elif section == "metrics":
                        section_overrides["include_metrics"] = False
                    elif section == "raw_response":
                        section_overrides["include_raw"] = False
                    elif section == "task_graph":
                        section_overrides["include_task_graph"] = False
                    elif section == "react_traces":
                        section_overrides["include_react_traces"] = False
                    elif section == "knowledge_graph":
                        section_overrides["include_knowledge_graph"] = False
                    elif section == "graph_exports":
                        section_overrides["include_graph_exports"] = False

        # Show a success message before the results
        print_success("Query processed successfully")

        OutputFormatter.format(
            result,
            fmt,
            depth=cast(Optional[OutputDepth], depth),
            section_overrides=section_overrides,
        )
        if result.state_id:
            print_info(
                f"State ID: {result.state_id}",
                symbol=False,
            )
            print_info(
                "Use `autoresearch reverify` to refresh claim audits with new sources.",
                symbol=False,
            )
        knowledge_meta = result.metrics.get("knowledge_graph")
        summary: Mapping[str, Any] | None = None
        exports_meta: Mapping[str, Any] | None = None
        if isinstance(knowledge_meta, Mapping):
            raw_summary = knowledge_meta.get("summary")
            raw_exports = knowledge_meta.get("exports")
            if isinstance(raw_summary, Mapping):
                summary = raw_summary
            if isinstance(raw_exports, Mapping):
                exports_meta = raw_exports

        summary_available = bool(summary)
        if summary_available:
            suggestions: list[str] = []

            def _add_suggestions(fmt_key: str) -> None:
                if fmt_key == "graphml":
                    suggestions.extend(["--graphml <path>", "--output graphml"])
                elif fmt_key == "graph_json":
                    suggestions.extend(["--graph-json <path>", "--output graph-json"])

            if exports_meta:
                if exports_meta.get("graphml"):
                    _add_suggestions("graphml")
                if exports_meta.get("graph_json"):
                    _add_suggestions("graph_json")
            if (
                not suggestions
                and summary
                and (summary.get("entity_count") or summary.get("relation_count"))
            ):
                _add_suggestions("graphml")
                _add_suggestions("graph_json")
            if suggestions:
                tips = " or ".join(dict.fromkeys(suggestions))
                print_info(
                    f"Graph exports available. Re-run with {tips} to download the knowledge graph."
                )

        raw_targets: dict[str, str | Path | None] = {
            "graphml": graphml,
            "graph_json": graph_json,
        }
        export_targets: dict[str, str | Path] = {
            fmt: target for fmt, target in raw_targets.items() if target is not None
        }
        if export_targets:
            if not summary_available:
                print_warning(
                    "Knowledge graph data is not available yet; skipping export commands."
                )
            else:
                for fmt, target in export_targets.items():
                    if fmt == "graphml":
                        export_data = StorageManager.export_knowledge_graph_graphml()
                        label = "GraphML"
                    else:
                        export_data = StorageManager.export_knowledge_graph_json()
                        label = "Graph JSON"
                    if not isinstance(export_data, str) or not export_data.strip():
                        print_warning(f"No {label.lower()} payload available to export.")
                        continue
                    if isinstance(target, Path) and str(target) == "-":
                        sys.stdout.write(export_data)
                        if not export_data.endswith("\n"):
                            sys.stdout.write("\n")
                        sys.stdout.flush()
                    else:
                        target_path = Path(target)
                        if target_path.is_dir():
                            target_path = target_path / (
                                f"knowledge_graph_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                                + (".graphml" if fmt == "graphml" else ".json")
                            )
                        target_path.parent.mkdir(parents=True, exist_ok=True)
                        target_path.write_text(export_data, encoding="utf-8")
                        print_success(f"{label} export written to {target_path}")

        if visualize:
            OutputFormatter.format(result, "graph")
            visualize_metrics_cli(result.metrics)
    except Exception as e:
        # Get error information with suggestions and code examples
        error_info = get_error_info(e)
        error_msg, suggestion, code_example = format_error_for_cli(error_info)

        # Create reasoning with suggestions for the error result
        reasoning = ["An error occurred during processing."]
        if error_info.suggestions:
            for suggestion in error_info.suggestions:
                reasoning.append(f"Suggestion: {suggestion}")
        else:
            reasoning.append("Please check the logs for details.")

        error_result = QueryResponse(
            answer=f"Error: {error_msg}",
            citations=[],
            reasoning=reasoning,
            metrics={
                "error": error_msg,
                "suggestions": error_info.suggestions,
                "code_examples": error_info.code_examples,
            },
        )

        # Format and output the error result (this replaces the separate error printing)
        fmt = output or (
            "markdown"
            if os.getenv("PYTEST_CURRENT_TEST")
            else ("json" if not sys.stdout.isatty() else "markdown")
        )
        OutputFormatter.format(error_result, fmt, depth=cast(Optional[OutputDepth], depth))

        # Print additional error details to stderr if verbose
        if get_verbosity() == Verbosity.VERBOSE:
            if error_info.traceback:
                print_verbose(f"Traceback:\n{''.join(error_info.traceback)}")
            else:
                import traceback

                print_verbose(f"Traceback:\n{traceback.format_exc()}")
        else:
            print_info("Run with --verbose for more details")


# Add monitoring subcommands
app.add_typer(monitor_app, name="monitor")


@typed_command()
def reverify(
    state_id: str = typer.Argument(
        ..., help="State ID emitted after a previous `autoresearch search` run"
    ),
    broaden_sources: bool = typer.Option(
        False,
        "--broaden-sources",
        help="Broaden retrieval by increasing max results and query variations.",
    ),
    max_results: Optional[int] = typer.Option(
        None,
        "--max-results",
        help="Explicit max results override for re-verification retrieval.",
    ),
    max_variations: Optional[int] = typer.Option(
        None,
        "--max-variations",
        help="Explicit limit for retrieval query variations during re-verification.",
    ),
    prompt_variant: Optional[str] = typer.Option(
        None,
        "--prompt-variant",
        help=(
            "Append a suffix to the `fact_checker.verification` prompt template. "
            "For example, `--prompt-variant aggressive` selects "
            "`fact_checker.verification.aggressive` if defined."
        ),
    ),
    output: Optional[str] = typer.Option(
        None, "-o", "--output", help="Output format: json|markdown|plain"
    ),
    depth: Optional[str] = typer.Option(
        None,
        "--depth",
        help=f"Depth of detail in CLI output ({depth_help_text()})",
        callback=depth_option_callback,
    ),
) -> None:
    """Re-run claim verification for a previously executed query."""

    from ..output_format import OutputFormatter

    try:
        options = ReverifyOptions(
            broaden_sources=broaden_sources,
            max_results=max_results,
            max_variations=max_variations,
            prompt_variant=prompt_variant or None,
        )
    except Exception as exc:  # pragma: no cover - defensive
        print_error("Invalid re-verification options", suggestion=str(exc))
        raise typer.Exit(code=1) from exc

    try:
        response = run_reverification(state_id, options=options)
    except LookupError as exc:
        print_error(f"No query state found for ID {state_id}")
        raise typer.Exit(code=1) from exc
    except Exception as exc:  # pragma: no cover - defensive
        error_info = get_error_info(exc)
        error_msg, suggestion, code_example = format_error_for_cli(error_info)
        print_error(
            f"Error refreshing claim audits: {error_msg}",
            suggestion=suggestion,
            code_example=code_example,
        )
        if get_verbosity() == Verbosity.VERBOSE:
            if error_info.traceback:
                print_verbose(f"Traceback:\n{''.join(error_info.traceback)}")
        else:
            print_info("Run with --verbose for more details")
        raise typer.Exit(code=1) from exc

    print_success("Claim verification refreshed")
    fmt = output or (
        "markdown"
        if os.getenv("PYTEST_CURRENT_TEST")
        else ("json" if not sys.stdout.isatty() else "markdown")
    )
    OutputFormatter.format(response, fmt, depth=cast(Optional[OutputDepth], depth))
    if response.state_id:
        print_info(f"State ID: {response.state_id}", symbol=False)


@typed_command()
def serve(
    host: str = typer.Option("127.0.0.1", "--host", help="Host to bind the MCP server to"),
    port: int = typer.Option(8080, "--port", "-p", help="Port to bind the MCP server to"),
) -> None:
    """Start an MCP server that exposes Autoresearch as a tool.

    This allows other LLM agents to use Autoresearch as a tool via the Model-Context Protocol.
    The server provides a research tool that can be used by other agents to perform research
    queries and get evidence-backed answers.

    Examples:
        # Start the MCP server on the default host and port
        autoresearch serve

        # Start the MCP server on a specific port
        autoresearch serve --port 9000

        # Start the MCP server on a specific host and port
        autoresearch serve --host 0.0.0.0 --port 8888
    """
    console = get_console()

    # Create an MCP server using the dedicated interface module
    server = create_server(host=host, port=port)

    console.print(
        render_status_panel(
            "MCP Server",
            f"Starting on {host}:{port}",
            status="success",
        )
    )
    console.print("Available tools:")
    console.print("  - research: Run a research query through Autoresearch")
    console.print()
    console.print(render_status_panel("", "Press Ctrl+C to stop the server"))

    try:
        server.run()
    except KeyboardInterrupt:
        console.print(render_status_panel("MCP Server", "Server stopped", status="warning"))
        raise typer.Exit(0)


@typed_command()
def serve_a2a(
    host: str = typer.Option("127.0.0.1", "--host", help="Host to bind the A2A server to"),
    port: int = typer.Option(8765, "--port", "-p", help="Port to bind the A2A server to"),
) -> None:
    """Start an A2A server that exposes Autoresearch as an agent.

    This allows other A2A-compatible agents to interact with Autoresearch via the
    Agent-to-Agent protocol. The server exposes Autoresearch's capabilities as an
    agent that can process queries, manage configuration, and discover capabilities.

    Examples:
        # Start the A2A server on the default host and port
        autoresearch serve_a2a

        # Start the A2A server on a specific port
        autoresearch serve_a2a --port 9000

        # Start the A2A server on a specific host and port
        autoresearch serve_a2a --host 0.0.0.0 --port 8765
    """
    try:
        from ..a2a_interface import A2AInterface
    except ImportError:
        console = get_console()
        console.print(
            render_status_panel(
                "A2A Server",
                "The a2a-sdk package is required for A2A integration.",
                status="error",
            )
        )
        console.print(render_status_panel("", "Install it with: pip install a2a-sdk"))
        return

    console = get_console()
    a2a_interface = None

    try:
        a2a_interface = A2AInterface(host=host, port=port)

        console.print(
            render_status_panel(
                "A2A Server",
                f"Starting on {host}:{port}",
                status="success",
            )
        )
        console.print("Available capabilities:")
        console.print("  - Query processing: Process natural language queries")
        console.print("  - Configuration management: Get and set configuration")
        console.print("  - Capability discovery: Discover LLM capabilities")
        console.print()
        console.print(render_status_panel("", "Press Ctrl+C to stop the server"))

        try:
            a2a_interface.start()
        except KeyboardInterrupt:
            if a2a_interface is not None:
                a2a_interface.stop()
            console.print(
                render_status_panel("A2A Server", "Server stopped", status="warning")
            )
            return

        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        if a2a_interface is not None:
            a2a_interface.stop()
        console.print(render_status_panel("A2A Server", "Server stopped", status="warning"))
        raise typer.Exit(code=0)
    except Exception as exc:
        console.print(
            render_status_panel(
                "A2A Server",
                f"Error starting server: {exc}",
                status="error",
            )
        )
        if a2a_interface is not None:
            a2a_interface.stop()
        raise typer.Exit(1)


@typed_command("completion")
def completion(
    shell: str = typer.Argument(
        ..., help="Shell to generate completion script for (bash, zsh, fish)"
    ),
    output_file: Optional[str] = typer.Option(
        None, "--output", "-o", help="Output file to write completion script to"
    ),
) -> None:
    """Generate shell completion script.

    This command generates a shell completion script for the specified shell.
    The script can be sourced to enable tab completion for autoresearch commands.

    Examples:
        # Generate bash completion script and save to a file
        autoresearch completion bash -o ~/.bash_completion.d/autoresearch.bash

        # Generate zsh completion script and print to stdout
        autoresearch completion zsh

        # Generate fish completion script and save to the default location
        autoresearch completion fish -o ~/.config/fish/completions/autoresearch.fish
    """
    from pathlib import Path

    # Validate shell
    valid_shells = ["bash", "zsh", "fish"]
    if shell not in valid_shells:
        print_error(
            f"Invalid shell: {shell}",
            suggestion=f"Valid shells are: {', '.join(valid_shells)}",
            code_example="autoresearch completion bash",
        )
        raise typer.Exit(1)

    # Get the completion script
    try:
        # Use typer's built-in completion script generation
        # We need to get the command that was used to run this script
        cmd = Path(sys.argv[0]).name

        if shell == "bash":
            completion_script = f"""
# {cmd} completion script for bash
_{cmd.upper()}_COMPLETE=bash_source {cmd} > /dev/null
source <(_{cmd.upper()}_COMPLETE=bash_source {cmd})
"""
        elif shell == "zsh":
            completion_script = f"""
# {cmd} completion script for zsh
_{cmd.upper()}_COMPLETE=zsh_source {cmd} > /dev/null
source <(_{cmd.upper()}_COMPLETE=zsh_source {cmd})
"""
        elif shell == "fish":
            completion_script = f"""
# {cmd} completion script for fish
_{cmd.upper()}_COMPLETE=fish_source {cmd} > /dev/null
_{cmd.upper()}_COMPLETE=fish_source {cmd} | source
"""

        # Write to file or print to stdout
        if output_file:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w") as f:
                f.write(completion_script)
            print_success(f"Completion script written to {output_file}")

            # Make the file executable
            os.chmod(output_path, 0o755)

            # Print instructions
            if shell == "bash":
                print_info("Add the following line to your ~/.bashrc:")
                print_command_example(f"source {output_file}")
            elif shell == "zsh":
                print_info("Add the following line to your ~/.zshrc:")
                print_command_example(f"source {output_file}")
            elif shell == "fish":
                print_info(f"The script has been installed to {output_file}")
                print_info("Fish will automatically load it from this location")
        else:
            # Print to stdout
            print(completion_script)

    except Exception as e:
        print_error(
            f"Error generating completion script: {e}",
            suggestion="Try specifying an output file with --output",
            code_example=f"autoresearch completion {shell} --output ~/autoresearch.{shell}",
        )
        raise typer.Exit(1)


@typed_command("capabilities")
def capabilities(
    output: Optional[str] = typer.Option(
        None, "-o", "--output", help="Output format: json|markdown|plain"
    ),
) -> None:
    """Discover the capabilities of the Autoresearch system.

    This command returns information about the capabilities of the Autoresearch system,
    including available reasoning modes, LLM backends, and other features. This information
    can be used to understand what functionality is available and how to use it.

    Examples:
        # Display capabilities in the default format
        autoresearch capabilities

        # Display capabilities in JSON format
        autoresearch capabilities --output json

        # Display capabilities in Markdown format
        autoresearch capabilities --output markdown
    """
    from ..llm.registry import get_available_adapters
    from ..orchestration.reasoning import ReasoningMode

    config = _config_loader.load_config()

    # Get available reasoning modes
    reasoning_modes = [mode.value for mode in ReasoningMode]

    # Get available LLM backends
    llm_backends = list(get_available_adapters().keys())

    # Get storage information
    storage_info = {
        "duckdb_path": config.storage.duckdb_path,
        "vector_extension": config.storage.vector_extension,
    }

    # Get search capabilities
    search_capabilities = {
        "max_results_per_query": config.search.max_results_per_query,
        "use_semantic_similarity": config.search.use_semantic_similarity,
    }

    # Get agent information
    agent_info = {
        "synthesizer": {
            "description": "Generates answers based on evidence",
            "role": "thesis",
        },
        "contrarian": {
            "description": "Challenges answers and identifies weaknesses",
            "role": "antithesis",
        },
        "factchecker": {
            "description": "Verifies factual accuracy of claims",
            "role": "synthesis",
        },
    }

    capabilities_data: dict[str, Any] = {
        "version": "1.0.0",
        "reasoning_modes": reasoning_modes,
        "llm_backends": llm_backends,
        "storage": storage_info,
        "search": search_capabilities,
        "agents": agent_info,
        "current_config": {
            "reasoning_mode": config.reasoning_mode.value,
            "loops": config.loops,
            "llm_backend": config.llm_backend,
        },
    }

    # Determine output format
    fmt = output or (
        "markdown"
        if os.getenv("PYTEST_CURRENT_TEST")
        else ("json" if not sys.stdout.isatty() else "markdown")
    )

    # Format and display the capabilities
    if fmt == "json":
        import json

        print(json.dumps(capabilities_data, indent=2))
    elif fmt == "plain":
        print("Autoresearch Capabilities:")
        print(f"Version: {capabilities_data['version']}")
        print("\nReasoning Modes:")
        for mode in capabilities_data["reasoning_modes"]:
            print(f"  - {mode}")
        print("\nLLM Backends:")
        for backend in capabilities_data["llm_backends"]:
            print(f"  - {backend}")
        print("\nStorage:")
        for key, value in capabilities_data["storage"].items():
            print(f"  - {key}: {value}")
        print("\nSearch:")
        for key, value in capabilities_data["search"].items():
            print(f"  - {key}: {value}")
        print("\nAgents:")
        for agent, info in capabilities_data["agents"].items():
            print(f"  - {agent}: {info['description']} (Role: {info['role']})")
        print("\nCurrent Configuration:")
        for key, value in capabilities_data["current_config"].items():
            print(f"  - {key}: {value}")
    else:  # markdown
        print("# Autoresearch Capabilities")
        print(f"Version: {capabilities_data['version']}")
        print("\n## Reasoning Modes")
        for mode in capabilities_data["reasoning_modes"]:
            print(f"- **{mode}**")
        print("\n## LLM Backends")
        for backend in capabilities_data["llm_backends"]:
            print(f"- **{backend}**")
        print("\n## Storage")
        for key, value in capabilities_data["storage"].items():
            print(f"- **{key}**: {value}")
        print("\n## Search")
        for key, value in capabilities_data["search"].items():
            print(f"- **{key}**: {value}")
        print("\n## Agents")
        for agent, info in capabilities_data["agents"].items():
            print(f"- **{agent}**: {info['description']} (Role: {info['role']})")
        print("\n## Current Configuration")
        for key, value in capabilities_data["current_config"].items():
            print(f"- **{key}**: {value}")


@typed_command("test_mcp")
def test_mcp(
    host: str = typer.Option("127.0.0.1", "--host", help="Host where the MCP server is running"),
    port: int = typer.Option(8080, "--port", "-p", help="Port where the MCP server is running"),
    query: Optional[str] = typer.Option(None, "--query", "-q", help="Query to test with"),
    output: Optional[str] = typer.Option(
        None, "-o", "--output", help="Output format: json|markdown|plain"
    ),
) -> None:
    """Test the MCP interface.

    This command tests the MCP interface by sending test requests and displaying the responses.
    It can test the connection to the MCP server and the research tool functionality.

    Examples:
        # Run a test suite with default queries
        autoresearch test_mcp

        # Run a test with a specific query
        autoresearch test_mcp --query "What is quantum computing?"

        # Run a test against a specific host and port
        autoresearch test_mcp --host 192.168.1.100 --port 8888

        # Output results in JSON format
        autoresearch test_mcp --output json
    """
    from ..test_tools import MCPTestClient, format_test_results

    # Create the MCP test client
    client = MCPTestClient(host=host, port=port)

    # Run tests
    if query:
        # Test with a specific query
        connection_test = client.test_connection()
        research_test = client.test_research_tool(query)
        results = {
            "connection_test": connection_test,
            "research_tests": [{"query": query, "result": research_test}],
        }
    else:
        # Run the full test suite
        results = client.run_test_suite()

    # Determine output format
    fmt = output or (
        "markdown"
        if os.getenv("PYTEST_CURRENT_TEST")
        else ("json" if not sys.stdout.isatty() else "markdown")
    )

    # Format and display the results
    formatted_results = format_test_results(results, fmt)
    print(formatted_results)


@typed_command("test_a2a")
def test_a2a(
    host: str = typer.Option("127.0.0.1", "--host", help="Host where the A2A server is running"),
    port: int = typer.Option(8765, "--port", "-p", help="Port where the A2A server is running"),
    query: Optional[str] = typer.Option(None, "--query", "-q", help="Query to test with"),
    output: Optional[str] = typer.Option(
        None, "-o", "--output", help="Output format: json|markdown|plain"
    ),
) -> None:
    """Test the A2A interface.

    This command tests the A2A interface by sending test requests and displaying the
    responses. It can test the connection to the A2A server, the capabilities
    endpoint, and the query functionality.

    Examples:
        # Run a test suite with default queries
        autoresearch test_a2a

        # Run a test with a specific query
        autoresearch test_a2a --query "What is quantum computing?"

        # Run a test against a specific host and port
        autoresearch test_a2a --host 192.168.1.100 --port 8765

        # Output results in JSON format
        autoresearch test_a2a --output json
    """
    from ..test_tools import A2ATestClient, format_test_results

    # Create the A2A test client
    client = A2ATestClient(host=host, port=port)

    # Run tests
    if query:
        # Test with a specific query
        connection_test = client.test_connection()
        capabilities_test = client.test_capabilities()
        query_test = client.test_query(query)
        results = {
            "connection_test": connection_test,
            "capabilities_test": capabilities_test,
            "query_tests": [{"query": query, "result": query_test}],
        }
    else:
        # Run the full test suite
        results = client.run_test_suite()

    # Determine output format
    fmt = output or (
        "markdown"
        if os.getenv("PYTEST_CURRENT_TEST")
        else ("json" if not sys.stdout.isatty() else "markdown")
    )

    # Format and display the results
    formatted_results = format_test_results(results, fmt)
    print(formatted_results)


@typed_command("visualize")
def visualize(
    query: str = typer.Argument(..., help="Query to visualize"),
    output: str = typer.Argument(..., help="Output PNG path for the visualization"),
    layout: str = typer.Option(
        "spring",
        "--layout",
        help="Graph layout algorithm (spring or circular)",
    ),
    interactive: bool = typer.Option(
        False,
        "--interactive",
        "-i",
        help="Refine the query interactively between agent cycles",
    ),
    loops: int | None = typer.Option(
        None,
        "--loops",
        help="Number of reasoning cycles to run",
    ),
    ontology: str | None = typer.Option(
        None,
        "--ontology",
        help="Load an ontology file before executing the query",
    ),
) -> None:
    """Run a query and render a knowledge graph."""
    try:
        # Call through the Typer app attribute so tests can monkeypatch it
        visualization_hooks.visualize_query(
            query,
            output,
            layout=layout,
            interactive=interactive,
            loops=loops,
            ontology=ontology,
        )
    except Exception:
        raise typer.Exit(1)


@typed_command("visualize-rdf")
def visualize_rdf_cli(
    output: str = typer.Argument(
        "rdf_graph.png",
        help="Output PNG path for the RDF graph visualization",
    ),
) -> None:
    """Generate a PNG visualization of the RDF knowledge graph."""
    try:
        # Call through the Typer app attribute so tests can monkeypatch it
        visualization_hooks.visualize(output)
    except Exception:
        raise typer.Exit(1)


@typed_command("sparql")
def sparql_query(
    query: str = typer.Argument(..., help="SPARQL query to run"),
    ontology_reasoner: Optional[str] = typer.Option(
        None,
        "--ontology-reasoner",
        "--reasoner",
        help="Ontology reasoner engine to apply",
    ),
    no_reasoning: bool = typer.Option(
        False,
        "--no-reasoning",
        help="Run the query without ontology reasoning",
    ),
) -> None:
    """Execute a SPARQL query with optional ontology reasoning."""
    try:
        _cli_sparql(query, engine=ontology_reasoner, apply_reasoning=not no_reasoning)
    except Exception:
        raise typer.Exit(1)


@typed_command("desktop")
def desktop() -> None:
    """
    Launch the PySide6 desktop application.

    This command starts the native desktop GUI for Autoresearch, providing
    a professional interface for research workflows with multi-window support,
    rich interactions, and native performance.

    The desktop interface provides:
    - Native desktop performance with GPU acceleration
    - Multi-window support for comparing queries
    - Rich interactions (drag-and-drop, annotations, keyboard shortcuts)
    - Professional appearance matching research tools
    - Offline-first operation (no server required)

    Examples:
        # Launch the desktop application
        autoresearch desktop

        # The application will open in a native window
        # Use the interface to run queries and view results
    """
    try:
        from ..ui.desktop.main import main as desktop_main
    except ImportError as e:
        print_error(
            f"Desktop interface not available: {e}",
            suggestion="Install the desktop extra with: uv sync --extra desktop",
        )
        raise typer.Exit(1)

    # Launch the desktop application
    desktop_main()


@typed_command("gui")
def gui(
    port: int = typer.Option(8501, "--port", "-p", help="Port to run the Streamlit app on"),
    browser: bool = typer.Option(True, "--browser/--no-browser", help="Open browser automatically"),
) -> None:
    """Launch the Streamlit GUI.

    This command launches a web-based GUI for Autoresearch using Streamlit.
    It provides a user-friendly interface for running queries, viewing results,
    and configuring settings.

    Examples:
        # Launch the GUI with default settings
        autoresearch gui

        # Launch the GUI on a specific port
        autoresearch gui --port 8502

        # Launch the GUI without opening a browser
        autoresearch gui --no-browser
    """
    import subprocess
    from pathlib import Path

    enable_flag = os.getenv("AUTORESEARCH_ENABLE_STREAMLIT")
    normalized_flag: Optional[str] = None
    is_opted_in = False
    if enable_flag is not None:
        normalized_flag = enable_flag.strip().lower()
        is_opted_in = normalized_flag in {"1", "true", "yes", "on"}

    if not is_opted_in:
        _dispatch_gui_event(
            "ui.legacy_gui.blocked",
            {
                "has_opt_in_flag": enable_flag is not None,
                "normalized_value": normalized_flag,
            },
        )
        print_warning(
            "The Streamlit GUI is deprecated and disabled by default during the "
            "PySide6 migration window.",
        )
        print_error(
            "Legacy Streamlit launch now requires an explicit opt-in.",
            suggestion=(
                "Re-run with AUTORESEARCH_ENABLE_STREAMLIT=1 autoresearch gui or use "
                "the PySide6 desktop interface via `autoresearch desktop`."
            ),
        )
        raise typer.Exit(1)

    # Get the path to the streamlit_app.py file
    # Go up two levels: from main/ to autoresearch/ where streamlit_app.py is located
    app_path = Path(__file__).parent.parent / "streamlit_app.py"

    # Ensure the file exists
    if not app_path.exists():
        print_error(
            f"Streamlit app file not found at {app_path}",
            suggestion="Make sure the streamlit_app.py file exists in the autoresearch package",
        )
        raise typer.Exit(1)

    # Build the command to run streamlit
    cmd = [
        "streamlit",
        "run",
        str(app_path),
        "--server.port",
        str(port),
    ]

    if not browser:
        cmd.extend(["--server.headless", "true"])

    _dispatch_gui_event(
        "ui.legacy_gui.launch",
        {
            "port": port,
            "browser": browser,
        },
    )

    print_info(f"Launching Streamlit GUI on port {port}...")
    print_info(f"URL: http://localhost:{port}")
    print_info("Press Ctrl+C to stop the server")

    try:
        # Run streamlit
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print_info("Streamlit GUI stopped")
    except Exception as e:
        print_error(
            f"Error launching Streamlit GUI: {e}",
            suggestion="Make sure Streamlit is installed and working correctly",
            code_example="pip install streamlit>=1.45.1",
        )
        raise typer.Exit(1)


if __name__ == "__main__":
    try:
        run_cli = cast(Callable[..., Any], app)
        run_cli()
    except typer.BadParameter as e:
        print_error(str(e))
        console.print("Run [cyan]autoresearch --help[/cyan] for more information.")
        sys.exit(1)
    except typer.Exit:
        # Re-raise typer.Exit to preserve exit code
        raise
    except Exception as e:
        # Handle command not found errors
        import sys

        cmd_name = sys.argv[1] if len(sys.argv) > 1 else ""
        if "No such command" in str(e) and cmd_name:
            # Create a dummy context for the handler
            context_cls = cast(Any, typer).Context
            ctx = context_cls(app)
            handle_command_not_found(ctx, cmd_name)
        else:
            # Re-raise other exceptions
            raise


@typed_command("diagnose-context")
def diagnose_context() -> None:
    """Diagnose context size capabilities and metrics.

    This command provides comprehensive diagnostics for context size management,
    including capabilities across providers, token counting accuracy, and
    utilization metrics.

    Examples:
        # Show context capabilities for all providers
        autoresearch diagnose-context

        # Include metrics from recent queries
        autoresearch diagnose-context
    """
    from ..llm.diagnostics import diagnose_context_full

    diagnose_context_full()
