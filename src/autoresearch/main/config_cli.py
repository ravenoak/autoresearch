from __future__ import annotations

from typing import Optional, Any

import typer

from ..config.models import ConfigModel
from ..config.loader import ConfigLoader
from ..errors import ConfigError
from .app import _config_loader
from ..cli_backup import backup_app

config_app = typer.Typer(help="Configuration management commands")


@config_app.callback(invoke_without_command=True)
def config_callback(ctx: typer.Context) -> None:
    """Manage configuration commands."""
    if ctx.invoked_subcommand is None:
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
    """Initialize configuration files with default values."""
    from pathlib import Path
    import shutil

    target_dir = Path(config_dir) if config_dir else Path.cwd()
    target_dir.mkdir(parents=True, exist_ok=True)
    toml_path = target_dir / "autoresearch.toml"
    env_path = target_dir / ".env"
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
    example_dir = Path(__file__).parent.parent.parent / "examples"
    example_toml = example_dir / "autoresearch.toml"
    example_env = example_dir / ".env.example"
    if not example_toml.exists():
        typer.echo(f"Example configuration file not found at {example_toml}.")
        return
    shutil.copy(example_toml, toml_path)
    typer.echo(f"Created configuration file at {toml_path}")
    if example_env.exists():
        shutil.copy(example_env, env_path)
        typer.echo(f"Created environment file at {env_path}")
    else:
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
    """Validate configuration files."""
    config_loader = ConfigLoader()
    search_paths = [p for p in config_loader.search_paths if p.exists()]
    env_path = config_loader.env_path
    if not search_paths:
        typer.echo("No configuration files found in search paths:")
        for path in config_loader.search_paths:
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


@config_app.command("reasoning")
def config_reasoning(
    loops: Optional[int] = typer.Option(None, help="Number of reasoning loops"),
    primus_start: Optional[int] = typer.Option(
        None, help="Index of starting agent for dialectical mode"
    ),
    mode: Optional[str] = typer.Option(None, help="Reasoning mode to use"),
    token_budget: Optional[int] = typer.Option(
        None, help="Token budget for a single run"
    ),
    max_errors: Optional[int] = typer.Option(
        None, help="Abort after this many errors"
    ),
    show: bool = typer.Option(
        False, "--show", help="Display current reasoning configuration"
    ),
) -> None:
    """Get or update reasoning configuration options."""
    cfg = _config_loader.load_config()
    data = cfg.model_dump()
    if show or not any(
        opt is not None for opt in (loops, primus_start, mode, token_budget, max_errors)
    ):
        typer.echo("Current reasoning settings:")
        typer.echo(f"  loops={data.get('loops')}")
        typer.echo(f"  primus_start={data.get('primus_start')}")
        typer.echo(f"  reasoning_mode={data.get('reasoning_mode')}")
        typer.echo(f"  token_budget={data.get('token_budget')}")
        typer.echo(f"  max_errors={data.get('max_errors', 3)}")
        return
    updates: dict[str, Any] = {}
    if loops is not None:
        updates["loops"] = loops
    if primus_start is not None:
        updates["primus_start"] = primus_start
    if mode is not None:
        updates["reasoning_mode"] = mode
    if token_budget is not None:
        updates["token_budget"] = token_budget
    if max_errors is not None:
        updates["max_errors"] = max_errors
    new_cfg = ConfigModel.model_validate({**data, **updates})
    path = _config_loader.search_paths[0]
    path.write_text(new_cfg.model_dump_json(indent=2))
    typer.echo(f"Updated {path}")


config_app.add_typer(backup_app, name="backup")
