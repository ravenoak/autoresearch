"""Typer commands for managing database backups."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt
from rich.progress import Progress
import typer
import time

from .storage_backup import BackupManager, BackupConfig
from .errors import BackupError

backup_app = typer.Typer(
    help="Backup and restore operations",
    context_settings={"allow_interspersed_args": True},
)


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
        config = BackupConfig(
            backup_dir=backup_dir or "backups",
            compress=compress,
            max_backups=max_backups,
            retention_days=retention_days,
        )
        with Progress() as progress:
            task = progress.add_task("[green]Creating backup...", total=1)
            backup_info = BackupManager.create_backup(
                backup_dir=backup_dir, compress=compress, config=config
            )
            progress.update(task, completed=1)

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
    """Restore a backup of the storage system."""
    console = Console()

    try:
        if not force:
            console.print(
                "[bold yellow]Warning:[/bold yellow] Restoring a backup will create new database files."
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
    """List available backups."""
    console = Console()

    try:
        backups = BackupManager.list_backups(backup_dir)
        if not backups:
            console.print(f"No backups found in {backup_dir or 'backups'}")
            return

        table = Table(title=f"Backups in {backup_dir or 'backups'}")
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
        BackupManager.schedule_backup(
            interval_hours=interval,
            backup_dir=backup_dir,
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
                "[bold yellow]Warning:[/bold yellow] Point-in-time recovery will create new database files."
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
            task = progress.add_task(
                "[green]Performing point-in-time recovery...", total=1
            )
            restored_paths = BackupManager.restore_point_in_time(
                backup_dir=backup_dir or "backups",
                target_time=target_time,
                target_dir=target_dir,
            )
            progress.update(task, completed=1)

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
