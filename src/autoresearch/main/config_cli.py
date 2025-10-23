from __future__ import annotations

from typing import Any, List, Optional

import importlib.resources as importlib_resources
import json

import tomli_w
import tomllib
import typer

from ..cli_backup import backup_app
from ..config.loader import ConfigLoader
from ..config_utils import validate_config
from ..errors import ConfigError, StorageError
from ..storage_utils import DEFAULT_NAMESPACE_LABEL, validate_namespace_routes
from .app import _config_loader

config_app = typer.Typer(help="Configuration management commands")


def _parse_route_entries(entries: List[str]) -> dict[str, str]:
    """Return normalized namespace routes from CLI inputs."""

    routes: dict[str, str] = {}
    if not entries:
        return routes
    valid_scopes = {"session", "workspace", "org", "project"}
    allowed_targets = valid_scopes | {"self"}
    for raw in entries:
        text = str(raw or "").strip()
        if not text:
            continue
        if "=" not in text:
            raise typer.BadParameter(
                "Route definitions must use scope=target format.", param_hint="--route"
            )
        scope, target = text.split("=", 1)
        scope_key = scope.strip().lower()
        target_key = target.strip().lower()
        if scope_key not in valid_scopes:
            raise typer.BadParameter(
                f"Unknown namespace scope '{scope_key}'. Valid scopes: session, workspace, org, project.",
                param_hint="--route",
            )
        if target_key not in allowed_targets:
            raise typer.BadParameter(
                f"Invalid route target '{target_key}'. Use session, workspace, org, project, or self.",
                param_hint="--route",
            )
        routes[scope_key] = target_key
    return routes


storage_app = typer.Typer(help="Manage storage configuration options")


@config_app.callback(invoke_without_command=True)
def config_callback(ctx: typer.Context) -> None:
    """Manage configuration commands."""
    invoked_subcommand = getattr(ctx, "invoked_subcommand", None)
    if invoked_subcommand is None:
        config = _config_loader.load_config()
        payload = config.model_dump(mode="python")
        typer.echo(json.dumps(payload, indent=2))


@storage_app.command("namespaces")
def storage_namespaces(
    default: Optional[str] = typer.Option(
        None,
        "--default",
        help="Set the default storage namespace label.",
        show_default=False,
    ),
    route: List[str] = typer.Option(
        [],
        "--route",
        "-r",
        help="Routing rule in scope=target form. Repeat to update multiple scopes.",
        show_default=False,
    ),
    reset: bool = typer.Option(
        False,
        "--reset",
        help="Restore the default namespace routing policy.",
    ),
    interactive: bool = typer.Option(
        False,
        "--interactive",
        "-i",
        help="Prompt for namespace defaults and route targets.",
    ),
    show: bool = typer.Option(
        False,
        "--show",
        help="Display the current namespace configuration without modifying it.",
    ),
) -> None:
    """Inspect or update storage namespace routing."""

    cfg = _config_loader.load_config()
    namespaces_cfg = cfg.storage.namespaces

    if show and not (default or route or reset or interactive):
        typer.echo("Current storage namespace configuration:")
        typer.echo(f"  default_namespace = {namespaces_cfg.default_namespace}")
        for scope, target in namespaces_cfg.routes.items():
            typer.echo(f"  route[{scope}] = {target}")
        if namespaces_cfg.merge_policies:
            typer.echo("  merge_policies:")
            for name, policy in namespaces_cfg.merge_policies.items():
                typer.echo(f"    {name}: {policy.model_dump(mode='python')}")
        return

    default_namespace = (default or namespaces_cfg.default_namespace or DEFAULT_NAMESPACE_LABEL).strip()
    if not default_namespace:
        default_namespace = DEFAULT_NAMESPACE_LABEL

    routes = dict(namespaces_cfg.routes)
    allowed_targets = {"session", "workspace", "org", "project", "self"}

    if reset:
        default_namespace = DEFAULT_NAMESPACE_LABEL
        routes = {"session": "workspace", "workspace": "project", "org": "project"}

    if route:
        routes.update(_parse_route_entries(route))

    if interactive or (not route and default is None and not reset and not show):
        default_namespace = (
            typer.prompt("Default namespace label", default=default_namespace)
            .strip()
            or DEFAULT_NAMESPACE_LABEL
        )
        fallback_targets = {"session": "workspace", "workspace": "project", "org": "project"}
        for scope in ("session", "workspace", "org"):
            current_target = routes.get(scope, fallback_targets[scope])
            while True:
                candidate = (
                    typer.prompt(f"Route target for {scope}", default=current_target)
                    .strip()
                    .lower()
                    or current_target
                )
                if candidate not in allowed_targets:
                    typer.echo(
                        "Invalid target. Choose from session, workspace, org, project, or self."
                    )
                    continue
                routes[scope] = candidate
                break

    try:
        validate_namespace_routes(routes)
    except StorageError as exc:
        raise typer.BadParameter(str(exc), param_hint="--route") from exc

    updated_namespaces = namespaces_cfg.model_copy(
        update={
            "default_namespace": default_namespace,
            "routes": routes,
        }
    )
    new_storage = cfg.storage.model_copy(update={"namespaces": updated_namespaces})
    new_cfg = cfg.model_copy(update={"storage": new_storage})

    path = next(
        (p for p in _config_loader.search_paths if p.exists()),
        _config_loader.search_paths[0],
    )
    try:
        existing = tomllib.loads(path.read_text()) if path.exists() else {}
    except Exception as exc:  # pragma: no cover - unexpected format
        raise ConfigError("Error reading config", file=str(path), cause=exc) from exc

    storage_section = existing.setdefault("storage", {})
    storage_section["namespaces"] = updated_namespaces.model_dump(mode="python")

    with open(path, "wb") as handle:
        tomli_w.dump(existing, handle)

    _config_loader._config = new_cfg
    typer.echo(f"Updated storage namespaces in {path}")


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

    target_dir = Path(config_dir) if config_dir else Path.cwd()
    target_dir.mkdir(parents=True, exist_ok=True)
    toml_path = target_dir / "autoresearch.toml"
    env_path = target_dir / ".env"
    if toml_path.exists() and not force:
        typer.echo(f"Configuration file already exists at {toml_path}. Use --force to overwrite.")
        return
    if env_path.exists() and not force:
        typer.echo(f"Environment file already exists at {env_path}. Use --force to overwrite.")
        return
    example_dir = importlib_resources.files("autoresearch.examples")
    example_toml = example_dir / "autoresearch.toml"
    example_env = example_dir / ".env.example"

    if not example_toml.is_file():
        typer.echo(f"Example configuration file not found at {example_toml}.")
        return

    toml_path.write_text(example_toml.read_text())
    typer.echo(f"Created configuration file at {toml_path}")

    if example_env.is_file():
        env_path.write_text(example_env.read_text())
        typer.echo(f"Created environment file at {env_path}")
    else:
        env_path.write_text(
            "# Autoresearch environment variables\n"
            "# Add your API keys and other secrets here\n\n"
            "# OpenAI API key\n"
            "# OPENAI_API_KEY=your-api-key\n"
        )
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
    valid, errors = validate_config(config_loader)
    if valid:
        typer.echo("Configuration is valid.")
    else:
        typer.echo("Configuration is invalid:")
        for err in errors:
            typer.echo(f"  - {err}")
        raise typer.Exit(code=1)


@config_app.command("reasoning")
def config_reasoning(
    loops: Optional[int] = typer.Option(None, help="Number of reasoning loops"),
    primus_start: Optional[int] = typer.Option(
        None, help="Index of starting agent for dialectical mode"
    ),
    mode: Optional[str] = typer.Option(None, help="Reasoning mode to use"),
    token_budget: Optional[int] = typer.Option(None, help="Token budget for a single run"),
    max_errors: Optional[int] = typer.Option(None, help="Abort after this many errors"),
    gate_policy_enabled: Optional[bool] = typer.Option(
        None, help="Enable scout gate heuristics (true/false)", show_default=False
    ),
    gate_retrieval_overlap_threshold: Optional[float] = typer.Option(
        None,
        help="Minimum retrieval overlap that still triggers debate",
        show_default=False,
    ),
    gate_nli_conflict_threshold: Optional[float] = typer.Option(
        None,
        help="Contradiction probability threshold for debate escalation",
        show_default=False,
    ),
    gate_complexity_threshold: Optional[float] = typer.Option(
        None,
        help="Complexity score threshold for debate escalation",
        show_default=False,
    ),
    gate_user_overrides: Optional[str] = typer.Option(
        None,
        help="JSON overrides for scout gate decisions",
        show_default=False,
    ),
    show: bool = typer.Option(False, "--show", help="Display current reasoning configuration"),
) -> None:
    """Get or update reasoning configuration options."""
    cfg = _config_loader.load_config()
    data = cfg.model_dump()
    if show or not any(
        opt is not None
        for opt in (
            loops,
            primus_start,
            mode,
            token_budget,
            max_errors,
            gate_policy_enabled,
            gate_retrieval_overlap_threshold,
            gate_nli_conflict_threshold,
            gate_complexity_threshold,
            gate_user_overrides,
        )
    ):
        typer.echo("Current reasoning settings:")
        typer.echo(f"  loops={data.get('loops')}")
        typer.echo(f"  primus_start={data.get('primus_start')}")
        typer.echo(f"  reasoning_mode={data.get('reasoning_mode')}")
        typer.echo(f"  token_budget={data.get('token_budget')}")
        typer.echo(f"  max_errors={data.get('max_errors', 3)}")
        typer.echo(f"  gate_policy_enabled={data.get('gate_policy_enabled')}")
        typer.echo(
            "  gate_retrieval_overlap_threshold=" f"{data.get('gate_retrieval_overlap_threshold')}"
        )
        typer.echo("  gate_nli_conflict_threshold=" f"{data.get('gate_nli_conflict_threshold')}")
        typer.echo("  gate_complexity_threshold=" f"{data.get('gate_complexity_threshold')}")
        typer.echo(f"  gate_user_overrides={data.get('gate_user_overrides')}")
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
            raise ConfigError(
                "Invalid JSON for gate_user_overrides",
                provided=gate_user_overrides,
                cause=exc,
            ) from exc
        if isinstance(overrides, dict):
            updates["gate_user_overrides"] = overrides
        else:
            raise ConfigError(
                "Invalid JSON for gate_user_overrides",
                provided=gate_user_overrides,
                cause=ValueError("Overrides must be a JSON object"),
            )
    new_cfg = cfg.model_copy(update=updates)
    path = next(
        (p for p in _config_loader.search_paths if p.exists()),
        _config_loader.search_paths[0],
    )
    try:
        existing = tomllib.loads(path.read_text()) if path.exists() else {}
    except Exception as e:  # pragma: no cover - unexpected format
        raise ConfigError("Error reading config", file=str(path), cause=e) from e
    core_cfg = existing.setdefault("core", {})
    core_cfg.update({k: v for k, v in updates.items()})
    with open(path, "wb") as f:
        tomli_w.dump(existing, f)
    _config_loader._config = new_cfg
    typer.echo(f"Updated {path}")


config_app.add_typer(storage_app, name="storage")
config_app.add_typer(backup_app, name="backup")
