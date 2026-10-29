from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from rich.console import Console
from rich.table import Table

from . import __version__
from .config import Settings, registry_path
from .models import OS_CHOICES, HealthStatus, Server, ValidationError
from .monitor import Monitor
from .registry import Registry, RegistryError
from .status import status_reason


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="kanslordash",
        description="Read-only fleet and network health dashboard.",
    )
    try:
        from . import __build_commit__

        if __build_commit__:
            parser.add_argument("--version", action="version", version=f"KanslorDash {__version__} ({__build_commit__})")
        else:
            parser.add_argument("--version", action="version", version=f"KanslorDash {__version__}")
    except Exception:
        parser.add_argument("--version", action="version", version=f"KanslorDash {__version__}")
    parser.add_argument("--registry", type=Path, default=None, help="Override the server registry path.")
    parser.add_argument("--refresh", type=int, default=None, help="Dashboard refresh interval in seconds.")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("list", help="List registered servers.")

    add = subparsers.add_parser("add", help="Add a server from the command line.")
    add.add_argument("name")
    add.add_argument("host")
    add.add_argument("--os", choices=OS_CHOICES, default="unknown")
    add.add_argument("--username", default="")
    add.add_argument("--port", type=int, default=22)
    add.add_argument("--tags", default="")
    add.add_argument("--disabled", action="store_true")

    remove = subparsers.add_parser("remove", help="Remove a server from the local registry.")
    remove.add_argument("name")
    remove.add_argument("--yes", action="store_true", help="Confirm removal without prompting.")

    check = subparsers.add_parser("check", help="Run one read-only health check.")
    check.add_argument("name", nargs="?", help="Server name; omit to check all servers.")
    check.add_argument("--json", action="store_true", dest="as_json")
    return parser


def _registry(args: argparse.Namespace) -> Registry:
    registry = Registry(args.registry or registry_path())
    registry.load()
    return registry


def _console() -> Console:
    return Console()


def _print_list(registry: Registry) -> None:
    servers = registry.list()
    console = _console()
    if not servers:
        console.print("[dim]No servers registered.[/dim]")
        return
    table = Table(title="KanslorDash Server Registry", show_lines=False)
    table.add_column("Name", style="bold cyan")
    table.add_column("Address")
    table.add_column("Platform")
    table.add_column("Tags")
    table.add_column("Enabled")
    for server in servers:
        table.add_row(
            server.name,
            f"{server.ssh_target}:{server.port}",
            server.os,
            ", ".join(server.tags) or "--",
            "yes" if server.enabled else "no",
        )
    console.print(table)


def _run_check(args: argparse.Namespace, registry: Registry) -> int:
    servers = registry.list()
    if args.name:
        server = registry.get(args.name)
        if server is None:
            _console().print(f"[red]Server {args.name!r} is not registered.[/red]")
            return 2
        servers = [server]
    settings = Settings()
    states = asyncio.run(Monitor(settings).collect_all(servers))
    if args.as_json:
        payload = [
            {
                "server": state.server.name,
                "address": state.server.address,
                "status": state.status.value,
                "reason": status_reason(state.server, state.connectivity, state.health),
                "latency_ms": state.connectivity.latency_ms if state.connectivity else None,
                "reachable": state.connectivity.reachable if state.connectivity else None,
                "ssh_open": state.connectivity.ssh_open if state.connectivity else None,
                "health": {
                    "hostname": state.health.hostname,
                    "os": state.health.os,
                    "uptime_seconds": state.health.uptime_seconds,
                    "load1": state.health.load1,
                    "cpu_percent": state.health.cpu_percent,
                    "mem_percent": state.health.mem_percent,
                    "disk_percent": state.health.disk_percent,
                    "temp_c": state.health.temp_c,
                    "failed_units": state.health.failed_units,
                    "updates": state.health.updates,
                    "error": state.health.error,
                }
                if state.health
                else None,
            }
            for state in states
        ]
        print(json.dumps(payload, indent=2))
        return 0

    console = _console()
    table = Table(title="KanslorDash Health Check")
    table.add_column("Server", style="bold")
    table.add_column("Status")
    table.add_column("Latency")
    table.add_column("Platform")
    table.add_column("Detail")
    colors = {
        HealthStatus.HEALTHY: "green",
        HealthStatus.DEGRADED: "yellow",
        HealthStatus.OFFLINE: "red",
        HealthStatus.UNKNOWN: "bright_black",
        HealthStatus.DISABLED: "bright_black",
    }
    for state in states:
        latency = (
            f"{state.connectivity.latency_ms:.0f} ms"
            if state.connectivity and state.connectivity.latency_ms is not None
            else "--"
        )
        table.add_row(
            state.server.name,
            f"[{colors[state.status]}]{state.status.symbol} {state.status.value}[/]",
            latency,
            state.server.os,
            status_reason(state.server, state.connectivity, state.health),
        )
    console.print(table)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        from .app import KanslorDashApp

        settings = Settings()
        if args.refresh is not None:
            settings.refresh_seconds = max(args.refresh, 0)
        app = KanslorDashApp(registry_file=args.registry, settings=settings)
        app.run()
        return 0

    try:
        registry = _registry(args)
    except RegistryError as error:
        _console().print(f"[red]{error}[/red]")
        return 1

    if args.command == "list":
        _print_list(registry)
        return 0
    if args.command == "add":
        try:
            server = Server(
                name=args.name,
                host=args.host,
                os=args.os,
                username=args.username,
                port=args.port,
                tags=args.tags,
                enabled=not args.disabled,
            )
            registry.add(server)
        except (ValidationError, RegistryError) as error:
            _console().print(f"[red]{error}[/red]")
            return 1
        _console().print(f"[green]Added {server.name} ({server.address}).[/green]")
        return 0
    if args.command == "remove":
        server = registry.get(args.name)
        if server is None:
            _console().print(f"[red]Server {args.name!r} is not registered.[/red]")
            return 2
        if not args.yes:
            _console().print("[yellow]Refusing to remove without --yes.[/yellow]")
            return 2
        registry.remove(server.id)
        _console().print(f"[green]Removed {server.name}.[/green]")
        return 0
    if args.command == "check":
        return _run_check(args, registry)

    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
