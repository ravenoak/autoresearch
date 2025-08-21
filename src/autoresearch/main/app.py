"""CLI entry point for Autoresearch with adaptive output formatting."""

from __future__ import annotations

import os
import sys
import time
from typing import Any, Optional

import typer
from rich.console import Console

from ..cli_helpers import handle_command_not_found, parse_agent_groups
from ..cli_utils import (
    Verbosity,
    console,
    format_success,
    get_verbosity,
    print_command_example,
    print_error,
    print_info,
    print_success,
    print_verbose,
    print_warning,
    set_verbosity,
)
from ..cli_utils import sparql_query_cli as _cli_sparql
from ..cli_utils import (
    visualize_metrics_cli,
)
from ..cli_utils import visualize_query_cli as _cli_visualize_query
from ..cli_utils import visualize_rdf_cli as _cli_visualize
from ..config.loader import ConfigLoader
from ..config.models import ConfigModel
from ..error_utils import format_error_for_cli, get_error_info
from ..errors import StorageError
from ..logging_utils import configure_logging
from ..mcp_interface import create_server
from ..monitor import monitor_app
from ..orchestration.orchestrator import Orchestrator
from ..orchestration.state import QueryState
from ..output_format import OutputFormatter
from ..storage import StorageManager

app = typer.Typer(
    help=(
        "Autoresearch CLI entry point.\n\n"
        "Set the reasoning mode using --mode or in autoresearch.toml under "
        "[core.reasoning_mode]. Valid values: direct, dialectical, "
        "chain-of-thought. Use --primus-start to choose the starting agent "
        "for dialectical reasoning."
    ),
    name="autoresearch",
    no_args_is_help=True,  # Show help when no arguments are provided
    pretty_exceptions_enable=False,
    # Disable pretty exceptions to handle them ourselves
)
# ``typer.Typer`` doesn't set ``name`` attribute on the object itself.
# ``click.testing.CliRunner`` expects a ``name`` attribute when invoking the
# application. Expose it explicitly so tests can run the CLI via ``CliRunner``.
app.name = "autoresearch"  # type: ignore[attr-defined]
configure_logging()
_config_loader: ConfigLoader = ConfigLoader()

from ..cli_backup import backup_app as _backup_app  # noqa: E402

from .config_cli import config_app as _config_app, config_init  # noqa: E402  # isort: skip

config_app = _config_app  # type: ignore[has-type]
app.add_typer(config_app, name="config")

backup_app = _backup_app
app.add_typer(backup_app, name="backup")


@app.callback(invoke_without_command=False)
def start_watcher(
    ctx: typer.Context,
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
    # Set environment variables for VSS extension control if CLI options are provided
    if no_vss:
        os.environ["VECTOR_EXTENSION"] = "false"
    if vss_path:
        os.environ["VECTOR_EXTENSION_PATH"] = vss_path

    # Check if this is the first run by looking for config files
    is_first_run = True
    for path in _config_loader.search_paths:
        if path.exists():
            is_first_run = False
            break

    # Show welcome message on first run
    if is_first_run and ctx.invoked_subcommand is None:
        console.print("\n" + format_success("Welcome to Autoresearch!", symbol=False))
        console.print(
            "A local-first research assistant that coordinates multiple agents to produce evidence-backed answers.\n"
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

    if ctx.invoked_subcommand != "config":
        try:
            StorageManager.setup()
        except StorageError as e:
            typer.echo(f"Storage initialization failed: {e}")
            raise typer.Exit(code=1)

    watch_ctx = _config_loader.watching()
    watch_ctx.__enter__()

    def _stop_watcher() -> None:
        try:
            watch_ctx.__exit__(None, None, None)
        finally:
            _config_loader.stop_watching()

    ctx.call_on_close(_stop_watcher)


@app.command()
def search(
    query: str = typer.Argument(..., help="Natural-language query to process"),
    output: Optional[str] = typer.Option(
        None, "-o", "--output", help="Output format: json|markdown|plain"
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
        help="Override reasoning mode for this run (direct, dialectical, chain-of-thought)",
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

        # Limit tokens and run multiple loops
        autoresearch search --loops 3 --token-budget 2000 "Explain AI ethics"

        # Adjust circuit breaker thresholds
        autoresearch search "Test" --circuit-breaker-threshold 5 --circuit-breaker-cooldown 60

        # Tune adaptive token budgeting
        autoresearch search "Long query" --adaptive-max-factor 25 --adaptive-min-buffer 20

        # Choose specific agents
        autoresearch search --agents Synthesizer,Contrarian "What is quantum computing?"

        # Run agent groups in parallel
        autoresearch search --parallel --agent-groups "Synthesizer,Contrarian" "FactChecker" "Impacts of AI"
    """
    config = _config_loader.load_config()

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
    if primus_start is not None:
        updates["primus_start"] = primus_start
    if agents is not None:
        updates["agents"] = [a.strip() for a in agents.split(",") if a.strip()]
    storage_updates: dict[str, Any] = {}
    if ontology_reasoner is not None:
        storage_updates["ontology_reasoner"] = ontology_reasoner
    if storage_updates:
        updates["storage"] = {**config.storage.model_dump(), **storage_updates}
    if updates:
        config = ConfigModel.model_validate({**config.model_dump(), **updates})

    if ontology:
        StorageManager.load_ontology(ontology)
    if ontology_reasoning:
        Orchestrator.infer_relations()

    # Check if query is empty or missing (this shouldn't happen with typer, but just in case)
    if not query or query.strip() == "":
        print_warning("You need to provide a query to search for.")
        print_command_example('autoresearch search "What is quantum computing?"', "Example query")
        print_command_example("autoresearch search --help", "Show help for search command")
        return

    try:
        loops = getattr(config, "loops", 1)

        from . import Progress, Prompt

        def on_cycle_end(loop: int, state: QueryState) -> None:
            progress.update(task, advance=1)
            if interactive and loop < loops - 1:
                refinement = Prompt.ask(
                    "Refine query or press Enter to continue (q to abort)",
                    default="",
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
                result = Orchestrator.run_parallel_query(query, config, groups)
            else:
                task = progress.add_task(
                    "[green]Processing query...",
                    total=loops,
                )
                result = Orchestrator().run_query(
                    query,
                    config,
                    callbacks={"on_cycle_end": on_cycle_end},
                    visualize=visualize,
                )

        fmt = output or (
            "markdown"
            if os.getenv("PYTEST_CURRENT_TEST")
            else ("json" if not sys.stdout.isatty() else "markdown")
        )

        # Show a success message before the results
        print_success("Query processed successfully")

        OutputFormatter.format(result, fmt)
        if visualize:
            OutputFormatter.format(result, "graph")
            visualize_metrics_cli(result.metrics)
    except Exception as e:
        # Create a valid QueryResponse object with error information
        from ..models import QueryResponse

        # Get error information with suggestions and code examples
        error_info = get_error_info(e)
        error_msg, suggestion, code_example = format_error_for_cli(error_info)

        # Log the error with a user-friendly message and suggestion
        print_error(
            f"Error processing query: {error_msg}",
            suggestion=suggestion,
            code_example=code_example,
        )

        if get_verbosity() == Verbosity.VERBOSE:
            if error_info.traceback:
                print_verbose(f"Traceback:\n{''.join(error_info.traceback)}")
            else:
                import traceback

                print_verbose(f"Traceback:\n{traceback.format_exc()}")
        else:
            print_info("Run with --verbose for more details")

        # Create reasoning with suggestions
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
        fmt = output or (
            "markdown"
            if os.getenv("PYTEST_CURRENT_TEST")
            else ("json" if not sys.stdout.isatty() else "markdown")
        )
        OutputFormatter.format(error_result, fmt)


# Add monitoring subcommands
app.add_typer(monitor_app, name="monitor")


@app.command()
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
    console = Console()

    # Create an MCP server using the dedicated interface module
    server = create_server(host=host, port=port)

    console.print(f"[bold green]Starting MCP server on {host}:{port}[/bold green]")
    console.print("Available tools:")
    console.print("  - research: Run a research query through Autoresearch")
    console.print("\nPress Ctrl+C to stop the server")

    try:
        server.run()
    except KeyboardInterrupt:
        console.print("[bold yellow]Server stopped[/bold yellow]")
        return


@app.command()
def serve_a2a(
    host: str = typer.Option("127.0.0.1", "--host", help="Host to bind the A2A server to"),
    port: int = typer.Option(8765, "--port", "-p", help="Port to bind the A2A server to"),
) -> None:
    """Start an A2A server that exposes Autoresearch as an agent.

    This allows other A2A-compatible agents to interact with Autoresearch via the Agent-to-Agent protocol.
    The server exposes Autoresearch's capabilities as an agent that can process queries, manage configuration,
    and discover capabilities.

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
        console = Console()
        console.print(
            "[bold red]Error:[/bold red] The a2a-sdk package is required for A2A integration."
        )
        console.print("Install it with: [bold]pip install a2a-sdk[/bold]")
        return

    console = Console()
    a2a_interface = None

    try:
        a2a_interface = A2AInterface(host=host, port=port)

        console.print(f"[bold green]Starting A2A server on {host}:{port}[/bold green]")
        console.print("Available capabilities:")
        console.print("  - Query processing: Process natural language queries")
        console.print("  - Configuration management: Get and set configuration")
        console.print("  - Capability discovery: Discover LLM capabilities")
        console.print("\nPress Ctrl+C to stop the server")

        # Start the server
        try:
            a2a_interface.start()
        except KeyboardInterrupt:
            if a2a_interface is not None:
                a2a_interface.stop()
            console.print("[bold yellow]Server stopped[/bold yellow]")
            return

        # Keep the main thread running until interrupted
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        if a2a_interface is not None:
            a2a_interface.stop()
        console.print("[bold yellow]Server stopped[/bold yellow]")
        raise typer.Exit(code=0)
    except Exception as e:
        console.print(f"[bold red]Error starting A2A server:[/bold red] {str(e)}")


@app.command("completion")
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


@app.command("capabilities")
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
    from .llm import get_available_adapters
    from .orchestration import ReasoningMode

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


@app.command("test_mcp")
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
    from .test_tools import MCPTestClient, format_test_results

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


@app.command("test_a2a")
def test_a2a(
    host: str = typer.Option("127.0.0.1", "--host", help="Host where the A2A server is running"),
    port: int = typer.Option(8765, "--port", "-p", help="Port where the A2A server is running"),
    query: Optional[str] = typer.Option(None, "--query", "-q", help="Query to test with"),
    output: Optional[str] = typer.Option(
        None, "-o", "--output", help="Output format: json|markdown|plain"
    ),
) -> None:
    """Test the A2A interface.

    This command tests the A2A interface by sending test requests and displaying the responses.
    It can test the connection to the A2A server, the capabilities endpoint, and the query functionality.

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
    from .test_tools import A2ATestClient, format_test_results

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


@app.command("visualize")
def visualize(
    query: str = typer.Argument(..., help="Query to visualize"),
    output: str = typer.Argument("query_graph.png", help="Output PNG path for the visualization"),
    layout: str = typer.Option(
        "spring",
        "--layout",
        help="Graph layout algorithm (spring or circular)",
    ),
) -> None:
    """Run a query and render a knowledge graph."""
    try:
        _cli_visualize_query(query, output, layout=layout)
    except Exception:
        raise typer.Exit(1)


@app.command("visualize-rdf")
def visualize_rdf_cli(
    output: str = typer.Argument(
        "rdf_graph.png",
        help="Output PNG path for the RDF graph visualization",
    ),
) -> None:
    """Generate a PNG visualization of the RDF knowledge graph."""
    try:
        _cli_visualize(output)
    except Exception:
        raise typer.Exit(1)


@app.command("sparql")
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


@app.command("gui")
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

    # Get the path to the streamlit_app.py file
    app_path = Path(__file__).parent / "streamlit_app.py"

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
        app()
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
            ctx = typer.Context(app)  # type: ignore[arg-type]
            handle_command_not_found(ctx, cmd_name)
        else:
            # Re-raise other exceptions
            raise
