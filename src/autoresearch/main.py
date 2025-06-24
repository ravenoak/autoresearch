"""CLI entry point for Autoresearch with adaptive output formatting."""

from __future__ import annotations

import sys
import os
import difflib
from typing import Optional, List, Sequence, Any
import click

import typer
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt
from rich.progress import Progress
from .mcp_interface import create_server
from .monitor import monitor_app
from datetime import datetime
import time

from .config import ConfigLoader, ConfigModel
from .orchestration.orchestrator import Orchestrator
from .orchestration.state import QueryState
from .output_format import OutputFormatter
from .logging_utils import configure_logging
from .storage import StorageManager
from .storage_backup import BackupManager, BackupConfig
from .errors import BackupError, StorageError
from .cli_utils import (
    console,
    print_success,
    print_error,
    print_warning,
    print_info,
    print_command_example,
    format_success,
    print_verbose,
    set_verbosity,
    get_verbosity,
    Verbosity,
    visualize_rdf_cli as _cli_visualize,
    sparql_query_cli as _cli_sparql,
)
from .error_utils import get_error_info, format_error_for_cli


def find_similar_commands(
    command: str, valid_commands: Sequence[str], threshold: float = 0.6
) -> List[str]:
    """Find similar commands to the given command.

    Args:
        command: The command to find similar commands for
        valid_commands: The list of valid commands
        threshold: The similarity threshold (0.0 to 1.0)

    Returns:
        A list of similar commands
    """
    # Use difflib to find similar commands
    matches = difflib.get_close_matches(
        command,
        valid_commands,
        n=3,
        cutoff=threshold,
    )
    return list(matches)


def handle_command_not_found(ctx: typer.Context, command: str) -> None:
    """Handle command not found errors with helpful suggestions.

    Args:
        ctx: The Typer context
        command: The command that was not found
    """
    print_error(f"Command '{command}' not found.")

    # Get all available commands
    available_commands: List[str] = []
    if isinstance(ctx.command, click.Group):
        for command_obj in ctx.command.commands.values():
            if command_obj.name:
                available_commands.append(command_obj.name)

    # Find similar commands
    similar_commands = find_similar_commands(command, available_commands)

    if similar_commands:
        print_info("Did you mean:", symbol=False)
        for cmd in similar_commands:
            print_command_example(cmd)

    console.print(
        "\nRun [cyan]autoresearch --help[/cyan] to see all available commands."
    )
    raise typer.Exit(code=1)


app = typer.Typer(
    help=(
        "Autoresearch CLI entry point.\n\n"
        "Set the reasoning mode in autoresearch.toml under "
        "[core.reasoning_mode]. Valid values: direct, dialectical, "
        "chain-of-thought."
    ),
    name="autoresearch",
    no_args_is_help=True,  # Show help when no arguments are provided
    pretty_exceptions_enable=False,
    # Disable pretty exceptions to handle them ourselves
)
configure_logging()
_config_loader: ConfigLoader = ConfigLoader()


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
    for path in _config_loader._search_paths:
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
        print_command_example(
            "monitor", "Start interactive resource and metrics monitor"
        )
        print_command_example("config", "Configuration management commands")
        print_command_example("backup", "Backup and restore operations")
        print_command_example("serve", "Start an MCP server")
        print_command_example("serve_a2a", "Start an A2A server")
        console.print("")

        print_command_example("autoresearch --help", "Show detailed help information")
        console.print("")

        # Suggest initializing configuration
        if typer.confirm(
            "Would you like to initialize the configuration now?", default=True
        ):
            ctx.invoke(config_init)
            return

    try:
        StorageManager.setup()
    except StorageError as e:
        typer.echo(f"Storage initialization failed: {e}")
        raise typer.Exit(code=1)

    watch_ctx = _config_loader.watching()
    watch_ctx.__enter__()
    ctx.call_on_close(lambda: watch_ctx.__exit__(None, None, None))


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
        help="Override reasoning mode for this run",
    ),
    primus_start: Optional[int] = typer.Option(
        None,
        "--primus-start",
        help="Starting agent index for dialectical reasoning",
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
    """
    config = _config_loader.load_config()

    updates: dict[str, Any] = {}
    if reasoning_mode is not None:
        updates["reasoning_mode"] = reasoning_mode
    if primus_start is not None:
        updates["primus_start"] = primus_start
    if updates:
        config = ConfigModel.model_validate({**config.model_dump(), **updates})

    # Check if query is empty or missing (this shouldn't happen with typer, but just in case)
    if not query or query.strip() == "":
        print_warning("You need to provide a query to search for.")
        print_command_example(
            'autoresearch search "What is quantum computing?"', "Example query"
        )
        print_command_example(
            "autoresearch search --help", "Show help for search command"
        )
        return

    try:
        loops = getattr(config, "loops", 1)

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
            task = progress.add_task("[green]Processing query...", total=loops)
            result = Orchestrator.run_query(
                query, config, callbacks={"on_cycle_end": on_cycle_end}
            )

        fmt = output or (
            "markdown"
            if os.getenv("PYTEST_CURRENT_TEST")
            else ("json" if not sys.stdout.isatty() else "markdown")
        )

        # Show a success message before the results
        print_success("Query processed successfully")

        OutputFormatter.format(result, fmt)
    except Exception as e:
        # Create a valid QueryResponse object with error information
        from .models import QueryResponse

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


config_app = typer.Typer(help="Configuration management commands")
app.add_typer(config_app, name="config")


@config_app.callback(invoke_without_command=True)
def config_callback(ctx: typer.Context) -> None:
    """Manage configuration commands."""
    if ctx.invoked_subcommand is None:
        # Display current configuration if no subcommand is provided
        config = _config_loader.load_config()
        typer.echo(config.json(indent=2))


@config_app.command("init")
def config_init(
    config_dir: Optional[str] = typer.Option(
        None,
        "--config-dir",
        "-d",
        help="Directory where configuration files will be created. Defaults to current directory.",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Overwrite existing configuration files.",
    ),
) -> None:
    """Initialize configuration files with default values.

    Creates autoresearch.toml and .env files in the specified directory.
    These files contain the default configuration for Autoresearch and can be
    customized to suit your needs.

    Examples:
        # Initialize configuration in the current directory
        autoresearch config init

        # Initialize configuration in a specific directory
        autoresearch config init --config-dir ~/autoresearch-config

        # Force overwrite of existing configuration files
        autoresearch config init --force
    """
    from pathlib import Path
    import shutil

    # Determine the target directory
    target_dir = Path(config_dir) if config_dir else Path.cwd()

    # Ensure the target directory exists
    target_dir.mkdir(parents=True, exist_ok=True)

    # Define paths for configuration files
    toml_path = target_dir / "autoresearch.toml"
    env_path = target_dir / ".env"

    # Check if files already exist
    if toml_path.exists() and not force:
        typer.echo(
            f"Configuration file already exists at {toml_path}. Use --force to overwrite."
        )
        return

    if env_path.exists() and not force:
        typer.echo(
            f"Environment file already exists at {env_path}. Use --force to overwrite."
        )
        return

    # Find the example configuration files
    example_dir = Path(__file__).parent.parent.parent / "examples"
    example_toml = example_dir / "autoresearch.toml"
    example_env = example_dir / ".env.example"

    if not example_toml.exists():
        typer.echo(f"Example configuration file not found at {example_toml}.")
        return

    # Copy the example files to the target directory
    shutil.copy(example_toml, toml_path)
    typer.echo(f"Created configuration file at {toml_path}")

    if example_env.exists():
        shutil.copy(example_env, env_path)
        typer.echo(f"Created environment file at {env_path}")
    else:
        # Create a basic .env file if the example doesn't exist
        with open(env_path, "w") as f:
            f.write("# Autoresearch environment variables\n")
            f.write("# Add your API keys and other secrets here\n\n")
            f.write("# OpenAI API key\n")
            f.write("# OPENAI_API_KEY=your-api-key\n")
        typer.echo(f"Created basic environment file at {env_path}")

    typer.echo("Configuration initialized successfully.")
    typer.echo("Edit these files to customize your configuration.")


@config_app.command("validate")
def config_validate() -> None:
    """Validate configuration files.

    Checks if the configuration files are valid and reports any errors.
    This command is useful for verifying that your configuration files
    are correctly formatted and contain valid values.

    Examples:
        # Validate configuration files
        autoresearch config validate
    """
    from .config import ConfigLoader, ConfigError

    config_loader = ConfigLoader()

    # Get the search paths from the config loader
    search_paths = [p for p in config_loader._search_paths if p.exists()]
    env_path = config_loader._env_path

    if not search_paths:
        typer.echo("No configuration files found in search paths:")
        for path in config_loader._search_paths:
            typer.echo(f"  - {path}")
        return

    typer.echo("Validating configuration files:")
    for path in search_paths:
        typer.echo(f"  - {path}")

    if env_path.exists():
        typer.echo(f"  - {env_path}")

    try:
        config_loader.load_config()
        typer.echo("Configuration is valid.")
    except ConfigError as e:
        typer.echo(f"Configuration error: {e}")
        return


# Add monitoring subcommands
app.add_typer(monitor_app, name="monitor")


@app.command()
def serve(
    host: str = typer.Option(
        "127.0.0.1", "--host", help="Host to bind the MCP server to"
    ),
    port: int = typer.Option(
        8080, "--port", "-p", help="Port to bind the MCP server to"
    ),
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


@app.command()
def serve_a2a(
    host: str = typer.Option(
        "127.0.0.1", "--host", help="Host to bind the A2A server to"
    ),
    port: int = typer.Option(
        8765, "--port", "-p", help="Port to bind the A2A server to"
    ),
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
        from .a2a_interface import A2AInterface
    except ImportError:
        console = Console()
        console.print(
            "[bold red]Error:[/bold red] The a2a-sdk package is required for A2A integration."
        )
        console.print("Install it with: [bold]pip install a2a-sdk[/bold]")
        return

    console = Console()

    # Create an A2A interface
    try:
        a2a_interface = A2AInterface(host=host, port=port)

        console.print(f"[bold green]Starting A2A server on {host}:{port}[/bold green]")
        console.print("Available capabilities:")
        console.print("  - Query processing: Process natural language queries")
        console.print("  - Configuration management: Get and set configuration")
        console.print("  - Capability discovery: Discover LLM capabilities")
        console.print("\nPress Ctrl+C to stop the server")

        # Start the server
        a2a_interface.start()

        # Keep the main thread running until interrupted
        try:
            import time

            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            a2a_interface.stop()
            console.print("[bold yellow]Server stopped[/bold yellow]")
    except Exception as e:
        console.print(f"[bold red]Error starting A2A server:[/bold red] {str(e)}")


backup_app = typer.Typer(help="Backup and restore operations")
app.add_typer(backup_app, name="backup")


@backup_app.command("create")
def backup_create(
    backup_dir: Optional[str] = typer.Option(
        None,
        "--dir",
        "-d",
        help="Directory where backups will be stored. Defaults to 'backups' or value from config.",
    ),
    compress: bool = typer.Option(
        True,
        "--compress/--no-compress",
        help="Whether to compress the backup. Default is to compress.",
    ),
    max_backups: int = typer.Option(
        5,
        "--max-backups",
        "-m",
        help="Maximum number of backups to keep. Default is 5.",
    ),
    retention_days: int = typer.Option(
        30,
        "--retention-days",
        "-r",
        help="Maximum age of backups in days. Default is 30.",
    ),
) -> None:
    """Create a backup of the storage system.

    This command creates a backup of the DuckDB database and RDF store.
    The backup can be compressed to save space, and a rotation policy
    can be applied to limit the number and age of backups.

    Examples:
        # Create a backup with default settings
        autoresearch backup create

        # Create a backup in a specific directory
        autoresearch backup create --dir ~/autoresearch-backups

        # Create an uncompressed backup
        autoresearch backup create --no-compress

        # Create a backup with custom retention settings
        autoresearch backup create --max-backups 10 --retention-days 60
    """
    console = Console()

    try:
        # Create backup configuration
        config = BackupConfig(
            backup_dir=backup_dir or "backups",
            compress=compress,
            max_backups=max_backups,
            retention_days=retention_days,
        )

        # Show progress
        with Progress() as progress:
            task = progress.add_task("[green]Creating backup...", total=1)

            # Create backup
            backup_info = BackupManager.create_backup(
                backup_dir=backup_dir, compress=compress, config=config
            )

            progress.update(task, completed=1)

        # Show backup info
        console.print("[bold green]Backup created successfully:[/bold green]")
        console.print(f"  Path: {backup_info.path}")
        console.print(f"  Timestamp: {backup_info.timestamp}")
        console.print(f"  Size: {_format_size(backup_info.size)}")
        console.print(f"  Compressed: {'Yes' if backup_info.compressed else 'No'}")

    except BackupError as e:
        console.print(f"[bold red]Error creating backup:[/bold red] {str(e)}")
        if hasattr(e, "context") and "suggestion" in e.context:
            console.print(f"[yellow]Suggestion:[/yellow] {e.context['suggestion']}")
        raise typer.Exit(code=1)


@backup_app.command("restore")
def backup_restore(
    backup_path: str = typer.Argument(
        ...,
        help="Path to the backup to restore. Use 'list' command to see available backups.",
    ),
    target_dir: Optional[str] = typer.Option(
        None,
        "--dir",
        "-d",
        help="Directory where the backup will be restored. Defaults to a timestamped directory.",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Force restore without confirmation.",
    ),
) -> None:
    """Restore a backup of the storage system.

    This command restores a backup of the DuckDB database and RDF store.
    The backup can be restored to a specific directory, or to a timestamped
    directory by default.

    Examples:
        # Restore a specific backup (first list backups to find the path)
        autoresearch backup restore backups/autoresearch-backup-2023-01-01-120000.tar.gz

        # Restore to a specific directory
        autoresearch backup restore backups/autoresearch-backup-2023-01-01-120000.tar.gz --dir ~/restored-data

        # Force restore without confirmation
        autoresearch backup restore backups/autoresearch-backup-2023-01-01-120000.tar.gz --force
    """
    console = Console()

    try:
        # Confirm restore if not forced
        if not force:
            console.print(
                "[bold yellow]Warning:[/bold yellow] Restoring a backup will create new database files."
            )
            console.print(
                "The original files will not be modified, but you will need to configure"
            )
            console.print(
                "the application to use the restored files if you want to use them."
            )
            confirm = Prompt.ask(
                "Are you sure you want to restore this backup?",
                choices=["y", "n"],
                default="n",
            )
            if confirm.lower() != "y":
                console.print("Restore cancelled.")
                return

        # Show progress
        with Progress() as progress:
            task = progress.add_task("[green]Restoring backup...", total=1)

            # Restore backup
            restored_paths = BackupManager.restore_backup(
                backup_path=backup_path, target_dir=target_dir
            )

            progress.update(task, completed=1)

        # Show restored paths
        console.print("[bold green]Backup restored successfully:[/bold green]")
        console.print(f"  DuckDB database: {restored_paths['db_path']}")
        console.print(f"  RDF store: {restored_paths['rdf_path']}")
        console.print(
            "\nTo use the restored files, update your configuration to point to these paths."
        )

    except BackupError as e:
        console.print(f"[bold red]Error restoring backup:[/bold red] {str(e)}")
        if hasattr(e, "context") and "suggestion" in e.context:
            console.print(f"[yellow]Suggestion:[/yellow] {e.context['suggestion']}")
        raise typer.Exit(code=1)


@backup_app.command("list")
def backup_list(
    backup_dir: Optional[str] = typer.Option(
        None,
        "--dir",
        "-d",
        help="Directory containing backups. Defaults to 'backups' or value from config.",
    ),
    limit: int = typer.Option(
        10,
        "--limit",
        "-n",
        help="Maximum number of backups to list. Default is 10.",
    ),
) -> None:
    """List available backups.

    This command lists all backups in the specified directory,
    showing their timestamp, size, and compression status.

    Examples:
        # List backups with default settings
        autoresearch backup list

        # List backups in a specific directory
        autoresearch backup list --dir ~/autoresearch-backups

        # List more backups than the default limit
        autoresearch backup list --limit 20
    """
    console = Console()

    try:
        # List backups
        backups = BackupManager.list_backups(backup_dir)

        if not backups:
            console.print(f"No backups found in {backup_dir or 'backups'}")
            return

        # Create table
        table = Table(title=f"Backups in {backup_dir or 'backups'}")
        table.add_column("Timestamp", style="cyan")
        table.add_column("Path", style="green")
        table.add_column("Size", style="magenta")
        table.add_column("Compressed", style="yellow")

        # Add rows
        for backup in backups[:limit]:
            table.add_row(
                backup.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                backup.path,
                _format_size(backup.size),
                "Yes" if backup.compressed else "No",
            )

        # Show table
        console.print(table)

        if len(backups) > limit:
            console.print(
                f"Showing {limit} of {len(backups)} backups. Use --limit to show more."
            )

    except BackupError as e:
        console.print(f"[bold red]Error listing backups:[/bold red] {str(e)}")
        if hasattr(e, "context") and "suggestion" in e.context:
            console.print(f"[yellow]Suggestion:[/yellow] {e.context['suggestion']}")
        raise typer.Exit(code=1)


@backup_app.command("schedule")
def backup_schedule(
    interval_hours: int = typer.Option(
        24,
        "--interval",
        "-i",
        help="Interval between backups in hours. Default is 24 (daily).",
    ),
    backup_dir: Optional[str] = typer.Option(
        None,
        "--dir",
        "-d",
        help="Directory where backups will be stored. Defaults to 'backups' or value from config.",
    ),
    compress: bool = typer.Option(
        True,
        "--compress/--no-compress",
        help="Whether to compress the backup. Default is to compress.",
    ),
    max_backups: int = typer.Option(
        5,
        "--max-backups",
        "-m",
        help="Maximum number of backups to keep. Default is 5.",
    ),
    retention_days: int = typer.Option(
        30,
        "--retention-days",
        "-r",
        help="Maximum age of backups in days. Default is 30.",
    ),
) -> None:
    """Schedule periodic backups.

    This command schedules periodic backups of the storage system.
    The backups will be created at the specified interval, and a
    rotation policy will be applied to limit the number and age of backups.

    Note: This command starts a background process that will continue
    running until the application is stopped.
    """
    console = Console()

    try:
        # Schedule backups
        BackupManager.schedule_backup(
            backup_dir=backup_dir,
            interval_hours=interval_hours,
            compress=compress,
            max_backups=max_backups,
            retention_days=retention_days,
        )

        console.print(
            f"[bold green]Scheduled backups every {interval_hours} hours to {backup_dir or 'backups'}[/bold green]"
        )
        console.print("The first backup will be created immediately.")
        console.print(
            "Press Ctrl+C to stop the application and cancel scheduled backups."
        )

        # Keep the application running
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            console.print("[bold yellow]Stopping scheduled backups...[/bold yellow]")
            BackupManager.stop_scheduled_backups()
            console.print("[bold green]Scheduled backups stopped.[/bold green]")

    except BackupError as e:
        console.print(f"[bold red]Error scheduling backups:[/bold red] {str(e)}")
        if hasattr(e, "context") and "suggestion" in e.context:
            console.print(f"[yellow]Suggestion:[/yellow] {e.context['suggestion']}")
        raise typer.Exit(code=1)


@backup_app.command("recover")
def backup_recover(
    timestamp: str = typer.Argument(
        ...,
        help="Target timestamp for point-in-time recovery (YYYY-MM-DD HH:MM:SS).",
    ),
    backup_dir: Optional[str] = typer.Option(
        None,
        "--dir",
        "-d",
        help="Directory containing backups. Defaults to 'backups' or value from config.",
    ),
    target_dir: Optional[str] = typer.Option(
        None,
        "--target-dir",
        "-t",
        help="Directory where the backup will be restored. Defaults to a timestamped directory.",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Force recovery without confirmation.",
    ),
) -> None:
    """Perform point-in-time recovery.

    This command restores the storage system to a specific point in time
    by finding the backup closest to the specified timestamp and restoring it.
    """
    console = Console()

    try:
        # Parse timestamp
        try:
            target_time = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            console.print(
                "[bold red]Error:[/bold red] Invalid timestamp format. Use YYYY-MM-DD HH:MM:SS."
            )
            raise typer.Exit(code=1)

        # Confirm recovery if not forced
        if not force:
            console.print(
                "[bold yellow]Warning:[/bold yellow] Point-in-time recovery will create new database files."
            )
            console.print(
                "The original files will not be modified, but you will need to configure"
            )
            console.print(
                "the application to use the recovered files if you want to use them."
            )
            confirm = Prompt.ask(
                "Are you sure you want to perform point-in-time recovery?",
                choices=["y", "n"],
                default="n",
            )
            if confirm.lower() != "y":
                console.print("Recovery cancelled.")
                return

        # Show progress
        with Progress() as progress:
            task = progress.add_task(
                "[green]Performing point-in-time recovery...", total=1
            )

            # Perform recovery
            restored_paths = BackupManager.restore_point_in_time(
                backup_dir=backup_dir or "backups",
                target_time=target_time,
                target_dir=target_dir,
            )

            progress.update(task, completed=1)

        # Show restored paths
        console.print(
            "[bold green]Point-in-time recovery completed successfully:[/bold green]"
        )
        console.print(f"  Target time: {target_time}")
        console.print(f"  DuckDB database: {restored_paths['db_path']}")
        console.print(f"  RDF store: {restored_paths['rdf_path']}")
        console.print(
            "\nTo use the recovered files, update your configuration to point to these paths."
        )

    except BackupError as e:
        console.print(
            f"[bold red]Error performing point-in-time recovery:[/bold red] {str(e)}"
        )
        if hasattr(e, "context") and "suggestion" in e.context:
            console.print(f"[yellow]Suggestion:[/yellow] {e.context['suggestion']}")
        raise typer.Exit(code=1)


def _format_size(size_bytes: int) -> str:
    """Format a size in bytes as a human-readable string."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


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
    host: str = typer.Option(
        "127.0.0.1", "--host", help="Host where the MCP server is running"
    ),
    port: int = typer.Option(
        8080, "--port", "-p", help="Port where the MCP server is running"
    ),
    query: Optional[str] = typer.Option(
        None, "--query", "-q", help="Query to test with"
    ),
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
    host: str = typer.Option(
        "127.0.0.1", "--host", help="Host where the A2A server is running"
    ),
    port: int = typer.Option(
        8765, "--port", "-p", help="Port where the A2A server is running"
    ),
    query: Optional[str] = typer.Option(
        None, "--query", "-q", help="Query to test with"
    ),
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
def sparql_query(query: str = typer.Argument(..., help="SPARQL query to run")) -> None:
    """Execute a SPARQL query with ontology reasoning."""
    try:
        _cli_sparql(query)
    except Exception:
        raise typer.Exit(1)


@app.command("gui")
def gui(
    port: int = typer.Option(
        8501, "--port", "-p", help="Port to run the Streamlit app on"
    ),
    browser: bool = typer.Option(
        True, "--browser/--no-browser", help="Open browser automatically"
    ),
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
