"""Typer commands for managing database backups."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt
from rich.progress import Progress
import typer
import time

from .storage_backup import BackupManager, BackupConfig
from .errors import BackupError
from .cli_helpers import report_missing_tables

backup_app = typer.Typer(
    help="Backup and restore operations",
)


def _render_backup_error(console: Console, prefix: str, error: BackupError) -> None:
    """Render a backup-related error with context information."""
    console.print(f"[bold red]{prefix}:[/bold red] {error}")
    ctx = getattr(error, "context", {}) or {}
    if "suggestion" in ctx:
        console.print(f"[yellow]Suggestion:[/yellow] {ctx['suggestion']}")
    if "missing_tables" in ctx:
        report_missing_tables(ctx["missing_tables"], console)


def _validate_dir(path: Optional[str], console: Console) -> str:
    """Validate that a path is a directory or can be created as one."""
    try:
        p = Path(path or "backups")
    except OSError as e:
        console.print(
            f"[bold red]Invalid backup directory:[/bold red] {path} ({e})"
        )
        raise typer.Exit(code=1)
    if p.exists() and not p.is_dir():
        console.print(
            f"[bold red]Invalid backup directory:[/bold red] {p} is not a directory"
        )
        raise typer.Exit(code=1)
    return str(p)


def _validate_file(path: str, console: Console) -> str:
    """Validate that a path points to an existing file."""
    try:
        p = Path(path)
    except OSError as e:
        console.print(f"[bold red]Invalid backup path:[/bold red] {path} ({e})")
        raise typer.Exit(code=1)
    if not p.exists() or not p.is_file():
        console.print(
            f"[bold red]Invalid backup path:[/bold red] {p} does not exist"
        )
        raise typer.Exit(code=1)
    return str(p)


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
    """Create a backup of the storage system."""
    console = Console()

    try:
        dir_path = _validate_dir(backup_dir, console)
        config = BackupConfig(
            backup_dir=dir_path,
            compress=compress,
            max_backups=max_backups,
            retention_days=retention_days,
        )
        with Progress() as progress:
            task = progress.add_task("[green]Creating backup...", total=1)
            backup_info = BackupManager.create_backup(
                backup_dir=dir_path, compress=compress, config=config
            )
            progress.update(task, completed=1)

        console.print("[bold green]Backup created successfully:[/bold green]")
        console.print(f"  Path: {backup_info.path}")
        console.print(f"  Timestamp: {backup_info.timestamp}")
        console.print(f"  Size: {_format_size(backup_info.size)}")
        console.print(f"  Compressed: {'Yes' if backup_info.compressed else 'No'}")

    except BackupError as e:
        _render_backup_error(console, "Error creating backup", e)
        raise typer.Exit(code=1)

    except KeyboardInterrupt:
        console.print("[bold yellow]Backup creation cancelled.[/bold yellow]")
        raise typer.Exit(code=1)

    except Exception as e:  # pragma: no cover - defensive
        console.print(f"[bold red]Unexpected error creating backup:[/bold red] {e}")
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
    """Restore a backup of the storage system."""
    console = Console()

    try:
        if not force:
            console.print(
                "[bold yellow]Warning:[/bold yellow] "
                "Restoring a backup will create new database files."
            )
            console.print("The original files will not be modified, but you will need to configure")
            console.print("the application to use the restored files if you want to use them.")
            confirm = Prompt.ask(
                "Are you sure you want to restore this backup?",
                choices=["y", "n"],
                default="n",
            )
            if confirm.lower() != "y":
                console.print("Restore cancelled.")
                return

        with Progress() as progress:
            task = progress.add_task("[green]Restoring backup...", total=1)
            restored_paths = BackupManager.restore_backup(
                backup_path=backup_path, target_dir=target_dir
            )
            progress.update(task, completed=1)

        console.print("[bold green]Backup restored successfully:[/bold green]")
        console.print(f"  DuckDB database: {restored_paths['db_path']}")
        console.print(f"  RDF store: {restored_paths['rdf_path']}")
        console.print(
            "\nTo use the restored files, update your configuration to point to these paths."
        )

    except BackupError as e:
        message = str(e).lower()
        if "not found" in message:
            console.print(
                f"[bold red]Invalid backup path:[/bold red] {backup_path} does not exist"
            )
        else:
            _render_backup_error(console, "Error restoring backup", e)
        raise typer.Exit(code=1)

    except KeyboardInterrupt:
        console.print("[bold yellow]Restore cancelled by user.[/bold yellow]")
        raise typer.Exit(code=1)

    except Exception as e:  # pragma: no cover - defensive
        console.print(f"[bold red]Unexpected error restoring backup:[/bold red] {e}")
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
    """List available backups."""
    console = Console()

    try:
        dir_path = _validate_dir(backup_dir, console)
        backups = BackupManager.list_backups(dir_path)
        if not backups:
            console.print(f"No backups found in {dir_path}")
            return

        table = Table(title=f"Backups in {dir_path}")
        table.add_column("Timestamp", style="cyan")
        table.add_column("Path", style="green")
        table.add_column("Size", style="magenta")
        table.add_column("Compressed", style="yellow")

        for backup in backups[:limit]:
            table.add_row(
                backup.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                backup.path,
                _format_size(backup.size),
                "Yes" if backup.compressed else "No",
            )

        console.print(table)

        if len(backups) > limit:
            console.print(f"Showing {limit} of {len(backups)} backups. Use --limit to show more.")

    except BackupError as e:
        _render_backup_error(console, "Error listing backups", e)
        raise typer.Exit(code=1)

    except KeyboardInterrupt:
        console.print("[bold yellow]Listing cancelled by user.[/bold yellow]")
        raise typer.Exit(code=1)

    except Exception as e:  # pragma: no cover - defensive
        console.print(f"[bold red]Unexpected error listing backups:[/bold red] {e}")
        raise typer.Exit(code=1)


@backup_app.command("schedule")
def backup_schedule(
    interval: int = typer.Option(
        24,
        "--interval",
        "-i",
        help="Interval in hours between automatic backups. Default is 24 hours.",
    ),
    backup_dir: Optional[str] = typer.Option(
        None,
        "--dir",
        "-d",
        help="Directory where backups will be stored. Defaults to 'backups' or value from config.",
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
    """Schedule automatic backups."""
    console = Console()

    try:
        dir_path = _validate_dir(backup_dir, console)
        BackupManager.schedule_backup(
            interval_hours=interval,
            backup_dir=dir_path,
            max_backups=max_backups,
            retention_days=retention_days,
        )
        console.print("[bold green]Scheduled automatic backups.[/bold green]")
        console.print("Press Ctrl+C to stop...")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            console.print("[bold yellow]Stopping scheduled backups...[/bold yellow]")
            BackupManager.stop_scheduled_backups()
            console.print("[bold green]Scheduled backups stopped.[/bold green]")

    except BackupError as e:
        _render_backup_error(console, "Error scheduling backups", e)
        raise typer.Exit(code=1)

    except KeyboardInterrupt:
        console.print("[bold yellow]Scheduling cancelled by user.[/bold yellow]")
        raise typer.Exit(code=1)

    except Exception as e:  # pragma: no cover - defensive
        console.print(f"[bold red]Unexpected error scheduling backups:[/bold red] {e}")
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
    """Perform point-in-time recovery."""
    console = Console()

    try:
        try:
            target_time = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            console.print(
                "[bold red]Error:[/bold red] Invalid timestamp format. Use YYYY-MM-DD HH:MM:SS."
            )
            raise typer.Exit(code=1)

        if not force:
            console.print(
                "[bold yellow]Warning:[/bold yellow] "
                "Point-in-time recovery will create new database files."
            )
            console.print("The original files will not be modified, but you will need to configure")
            console.print("the application to use the recovered files if you want to use them.")
            confirm = Prompt.ask(
                "Are you sure you want to perform point-in-time recovery?",
                choices=["y", "n"],
                default="n",
            )
            if confirm.lower() != "y":
                console.print("Recovery cancelled.")
                return

        with Progress() as progress:
            task = progress.add_task("[green]Performing point-in-time recovery...", total=1)
            dir_path = _validate_dir(backup_dir, console)
            restored_paths = BackupManager.restore_point_in_time(
                backup_dir=dir_path,
                target_time=target_time,
                target_dir=target_dir,
            )
            progress.update(task, completed=1)

        console.print("[bold green]Point-in-time recovery completed successfully:[/bold green]")
        console.print(f"  Target time: {target_time}")
        console.print(f"  DuckDB database: {restored_paths['db_path']}")
        console.print(f"  RDF store: {restored_paths['rdf_path']}")
        console.print(
            "\nTo use the recovered files, update your configuration to point to these paths."
        )

    except BackupError as e:
        _render_backup_error(
            console, "Error performing point-in-time recovery", e
        )
        raise typer.Exit(code=1)

    except KeyboardInterrupt:
        console.print("[bold yellow]Recovery cancelled by user.[/bold yellow]")
        raise typer.Exit(code=1)

    except Exception as e:  # pragma: no cover - defensive
        console.print(
            f"[bold red]Unexpected error performing point-in-time recovery:[/bold red] {e}"
        )
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
