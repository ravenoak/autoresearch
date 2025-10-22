"""CLI entrypoints for node health monitoring."""

from __future__ import annotations

import time
from typing import Optional

import typer

from ..cli_utils import get_console, render_status_panel
from . import monitor_app
from .node_health import NodeHealthMonitor

console = get_console()


@monitor_app.command("serve")
def serve(
    redis_url: Optional[str] = typer.Option(
        None, "--redis-url", help="Redis connection URL to check."
    ),
    ray_address: Optional[str] = typer.Option(
        None, "--ray-address", help="Ray cluster address to verify."
    ),
    port: int = typer.Option(8000, "--port", help="Port for the Prometheus server."),
    interval: float = typer.Option(5.0, "--interval", help="Health check interval in seconds."),
) -> None:
    """Expose node health metrics via a Prometheus endpoint.

    Args:
        redis_url: Redis connection URL to check.
        ray_address: Ray cluster address to verify.
        port: Port for the Prometheus server.
        interval: Health check interval in seconds.
    """
    console = get_console()
    monitor = NodeHealthMonitor(
        redis_url=redis_url, ray_address=ray_address, port=port, interval=interval
    )

    console.print(
        render_status_panel(
            "Node Health",
            f"Starting Prometheus exporter on port {port}",
            status="success",
        )
    )
    console.print(render_status_panel("", "Press Ctrl+C to stop the server"))

    try:
        monitor.start()
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        console.print(render_status_panel("Node Health", "Server stopped", status="warning"))
    finally:
        monitor.stop()

    raise typer.Exit(0)
