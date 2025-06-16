"""CLI entry point for Autoresearch with adaptive output formatting."""

from __future__ import annotations

import sys
import os
import json
from typing import Optional, Dict, Any, List

import typer
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt
from rich.progress import Progress
from mcp.server import Server
from mcp import Tool
from datetime import datetime

from .config import ConfigLoader
from .orchestration.orchestrator import Orchestrator
from .orchestration.state import QueryState
from .output_format import OutputFormatter
from .logging_utils import configure_logging
from .storage import StorageManager
from .storage_backup import BackupManager, BackupConfig, BackupInfo
from .errors import BackupError

app = typer.Typer(
    help=(
        "Autoresearch CLI entry point.\n\n"
        "Set the reasoning mode in autoresearch.toml under "
        "[core.reasoning_mode]. Valid values: direct, dialectical, "
        "chain-of-thought."
    ),
    name="autoresearch",
)
configure_logging()
_config_loader: ConfigLoader = ConfigLoader()


@app.callback(invoke_without_command=False)
def start_watcher(
    ctx: typer.Context,
    vss_path: Optional[str] = typer.Option(
        None,
        "--vss-path",
        help="Path to VSS extension file. Overrides config and environment settings.",
    ),
    no_vss: bool = typer.Option(
        False,
        "--no-vss",
        help="Disable VSS extension loading even if enabled in config.",
    ),
) -> None:
    """Start configuration watcher before executing commands."""
    # Set environment variables for VSS extension control if CLI options are provided
    if no_vss:
        os.environ["VECTOR_EXTENSION"] = "false"
    if vss_path:
        os.environ["VECTOR_EXTENSION_PATH"] = vss_path

    StorageManager.setup()
    watch_ctx = _config_loader.watching()
    watch_ctx.__enter__()
    ctx.call_on_close(lambda: watch_ctx.__exit__(None, None, None))


@app.command()
def search(
    query: str = typer.Argument(..., help="Natural-language query to process"),
    output: Optional[str] = typer.Option(
        None, "-o", "--output", help="Output format: json|markdown|plain"
    ),
) -> None:
    """Run a search query through the orchestrator and format the result."""
    config = _config_loader.load_config()
    console = Console()

    try:
        result = Orchestrator.run_query(query, config)
        fmt = output or (
            "markdown"
            if os.getenv("PYTEST_CURRENT_TEST")
            else ("json" if not sys.stdout.isatty() else "markdown")
        )
        OutputFormatter.format(result, fmt)
    except Exception as e:
        # Create a valid QueryResponse object with error information
        from .models import QueryResponse
        error_result = QueryResponse(
            answer=f"Error: {str(e)}",
            citations=[],
            reasoning=["An error occurred during processing.", "Please check the logs for details."],
            metrics={"error": str(e)}
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
    """Configuration management commands."""
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
        typer.echo(f"Configuration file already exists at {toml_path}. Use --force to overwrite.")
        return

    if env_path.exists() and not force:
        typer.echo(f"Environment file already exists at {env_path}. Use --force to overwrite.")
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
    """
    from pathlib import Path
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
        config = config_loader.load_config()
        typer.echo("Configuration is valid.")
    except ConfigError as e:
        typer.echo(f"Configuration error: {e}")
        return


@app.command()
def monitor() -> None:
    """Start interactive resource and metrics monitor (TUI)."""
    console = Console()
    config = _config_loader.load_config()

    abort_flag = {"stop": False}

    def on_cycle_end(loop: int, state: QueryState) -> None:
        metrics = state.metadata.get("execution_metrics", {})
        table = Table(title=f"Cycle {loop + 1} Metrics")
        table.add_column("Metric")
        table.add_column("Value")
        for k, v in metrics.items():
            table.add_row(str(k), str(v))
        console.print(table)
        feedback = Prompt.ask("Feedback (q to stop)", default="")
        if feedback.lower() == "q":
            state.error_count = getattr(config, "max_errors", 3)
            abort_flag["stop"] = True
        elif feedback:
            state.claims.append({"type": "feedback", "text": feedback})

    while True:
        query = Prompt.ask("Enter query (q to quit)")
        if not query or query.lower() == "q":
            break

        try:
            result = Orchestrator.run_query(
                query, config, {"on_cycle_end": on_cycle_end}
            )
            fmt = config.output_format or (
                "json" if not sys.stdout.isatty() else "markdown"
            )
            OutputFormatter.format(result, fmt)
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {str(e)}")
            # Continue with the next query instead of exiting with error

        if abort_flag["stop"]:
            break


@app.command()
def serve(
    host: str = typer.Option("127.0.0.1", "--host", help="Host to bind the MCP server to"),
    port: int = typer.Option(8080, "--port", "-p", help="Port to bind the MCP server to"),
) -> None:
    """Start an MCP server that exposes Autoresearch as a tool.

    This allows other LLM agents to use Autoresearch as a tool via the Model-Context Protocol.
    """
    config = _config_loader.load_config()
    console = Console()

    # Create an MCP server
    server = Server("Autoresearch", host=host, port=port)

    @server.tool
    def research(query: str) -> Dict[str, Any]:
        """Run a research query through Autoresearch and return the results.

        Args:
            query: The natural language query to research

        Returns:
            A dictionary containing the research results with answer, citations, and reasoning
        """
        try:
            result = Orchestrator.run_query(query, config)
            # Convert the QueryResponse to a dictionary
            return {
                "answer": result.answer,
                "citations": [citation.dict() for citation in result.citations],
                "reasoning": result.reasoning,
                "metrics": result.metrics
            }
        except Exception as e:
            return {
                "error": str(e),
                "answer": f"Error: {str(e)}",
                "citations": [],
                "reasoning": ["An error occurred during processing.", "Please check the logs for details."],
                "metrics": {"error": str(e)}
            }

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
    host: str = typer.Option("127.0.0.1", "--host", help="Host to bind the A2A server to"),
    port: int = typer.Option(8765, "--port", "-p", help="Port to bind the A2A server to"),
) -> None:
    """Start an A2A server that exposes Autoresearch as an agent.

    This allows other A2A-compatible agents to interact with Autoresearch via the Agent-to-Agent protocol.
    """
    try:
        from .a2a_interface import A2AInterface
    except ImportError:
        console = Console()
        console.print("[bold red]Error:[/bold red] The a2a-sdk package is required for A2A integration.")
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
    """
    console = Console()

    try:
        # Create backup configuration
        config = BackupConfig(
            backup_dir=backup_dir or "backups",
            compress=compress,
            max_backups=max_backups,
            retention_days=retention_days
        )

        # Show progress
        with Progress() as progress:
            task = progress.add_task("[green]Creating backup...", total=1)

            # Create backup
            backup_info = BackupManager.create_backup(
                backup_dir=backup_dir,
                compress=compress,
                config=config
            )

            progress.update(task, completed=1)

        # Show backup info
        console.print(f"[bold green]Backup created successfully:[/bold green]")
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
    """
    console = Console()

    try:
        # Confirm restore if not forced
        if not force:
            console.print("[bold yellow]Warning:[/bold yellow] Restoring a backup will create new database files.")
            console.print("The original files will not be modified, but you will need to configure")
            console.print("the application to use the restored files if you want to use them.")
            confirm = Prompt.ask("Are you sure you want to restore this backup?", choices=["y", "n"], default="n")
            if confirm.lower() != "y":
                console.print("Restore cancelled.")
                return

        # Show progress
        with Progress() as progress:
            task = progress.add_task("[green]Restoring backup...", total=1)

            # Restore backup
            restored_paths = BackupManager.restore_backup(
                backup_path=backup_path,
                target_dir=target_dir
            )

            progress.update(task, completed=1)

        # Show restored paths
        console.print(f"[bold green]Backup restored successfully:[/bold green]")
        console.print(f"  DuckDB database: {restored_paths['db_path']}")
        console.print(f"  RDF store: {restored_paths['rdf_path']}")
        console.print("\nTo use the restored files, update your configuration to point to these paths.")

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
                "Yes" if backup.compressed else "No"
            )

        # Show table
        console.print(table)

        if len(backups) > limit:
            console.print(f"Showing {limit} of {len(backups)} backups. Use --limit to show more.")

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
            retention_days=retention_days
        )

        console.print(f"[bold green]Scheduled backups every {interval_hours} hours to {backup_dir or 'backups'}[/bold green]")
        console.print("The first backup will be created immediately.")
        console.print("Press Ctrl+C to stop the application and cancel scheduled backups.")

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
            console.print("[bold red]Error:[/bold red] Invalid timestamp format. Use YYYY-MM-DD HH:MM:SS.")
            raise typer.Exit(code=1)

        # Confirm recovery if not forced
        if not force:
            console.print("[bold yellow]Warning:[/bold yellow] Point-in-time recovery will create new database files.")
            console.print("The original files will not be modified, but you will need to configure")
            console.print("the application to use the recovered files if you want to use them.")
            confirm = Prompt.ask("Are you sure you want to perform point-in-time recovery?", choices=["y", "n"], default="n")
            if confirm.lower() != "y":
                console.print("Recovery cancelled.")
                return

        # Show progress
        with Progress() as progress:
            task = progress.add_task("[green]Performing point-in-time recovery...", total=1)

            # Perform recovery
            restored_paths = BackupManager.restore_point_in_time(
                backup_dir=backup_dir or "backups",
                target_time=target_time,
                target_dir=target_dir
            )

            progress.update(task, completed=1)

        # Show restored paths
        console.print(f"[bold green]Point-in-time recovery completed successfully:[/bold green]")
        console.print(f"  Target time: {target_time}")
        console.print(f"  DuckDB database: {restored_paths['db_path']}")
        console.print(f"  RDF store: {restored_paths['rdf_path']}")
        console.print("\nTo use the recovered files, update your configuration to point to these paths.")

    except BackupError as e:
        console.print(f"[bold red]Error performing point-in-time recovery:[/bold red] {str(e)}")
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


if __name__ == "__main__":
    app()
