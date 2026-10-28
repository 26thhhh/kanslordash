from __future__ import annotations

from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Static

from ...models import HealthStatus, Server, ServerState
from ...status import status_reason

STATUS_COLORS = {
    HealthStatus.HEALTHY: "green",
    HealthStatus.DEGRADED: "yellow",
    HealthStatus.OFFLINE: "red",
    HealthStatus.UNKNOWN: "bright_black",
    HealthStatus.DISABLED: "bright_black",
}


class DashboardScreen(Screen):
    BINDINGS = [
        Binding("a", "add_server", "Add"),
        Binding("e", "edit_server", "Edit"),
        Binding("r", "remove_server", "Remove"),
        Binding("s", "ssh", "SSH"),
        Binding("d", "details", "Details"),
        Binding("n", "network", "Network"),
        Binding("t", "troubleshoot", "Troubleshoot"),
        Binding("f5", "refresh", "Refresh"),
        Binding("q", "quit", "Quit"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.selected_id: str | None = None

    def compose(self) -> ComposeResult:
        with Vertical(id="frame"):
            yield Static("K A N S L O R D A S H", id="banner")
            yield Static("READ-ONLY FLEET MONITOR // v1", id="subtitle")
            yield DataTable(id="servers", cursor_type="row", zebra_stripes=True)
            yield Static(id="summary")
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#servers", DataTable)
        table.add_columns("SERVER", "STATE", "HEALTH", "LATENCY", "PLATFORM", "CHECKED")
        self.render_states(self.app.states, self.app.servers())
        table.focus()

    def render_states(self, states: dict[str, ServerState], servers: list[Server]) -> None:
        table = self.query_one("#servers", DataTable)
        table.clear()
        for server in servers:
            state = states.get(server.id, ServerState(server=server))
            table.add_row(
                self._server_text(server),
                self._status_text(state),
                self._health_text(state),
                self._latency_text(state),
                server.os,
                self._checked_text(state),
                key=server.id,
            )
        if self.selected_id and self.selected_id in {server.id for server in servers}:
            index = next(index for index, server in enumerate(servers) if server.id == self.selected_id)
            table.move_cursor(row=index)
        elif servers:
            self.selected_id = servers[0].id
            table.move_cursor(row=0)
        self._update_summary(servers)

    def _server_text(self, server: Server) -> Text:
        tags = f" [{'/'.join(server.tags)}]" if server.tags else ""
        suffix = "" if server.enabled else " (disabled)"
        return Text(f"{server.name}{suffix}{tags}")

    def _status_text(self, state: ServerState) -> Text:
        return Text(f"{state.status.symbol} {state.status.value}", style=STATUS_COLORS[state.status])

    def _health_text(self, state: ServerState) -> str:
        health = state.health
        if health is None:
            return "--"
        pieces = []
        if health.cpu_percent is not None:
            pieces.append(f"cpu {health.cpu_percent:.0f}%")
        elif health.load1 is not None:
            pieces.append(f"load {health.load1:.2f}")
        if health.mem_percent is not None:
            pieces.append(f"mem {health.mem_percent:.0f}%")
        if health.disk_percent is not None:
            pieces.append(f"disk {health.disk_percent:.0f}%")
        if health.temp_c is not None:
            pieces.append(f"{health.temp_c:.0f}C")
        if health.failed_units:
            pieces.append(f"{health.failed_units} failed")
        return " | ".join(pieces) if pieces else "--"

    def _latency_text(self, state: ServerState) -> str:
        connectivity = state.connectivity
        if connectivity is None:
            return "--"
        if connectivity.ssh_open and connectivity.latency_ms is not None:
            return f"{connectivity.latency_ms:.0f} ms"
        if connectivity.reachable:
            return "ICMP"
        return "--"

    def _checked_text(self, state: ServerState) -> str:
        if state.checked_at is None:
            return "never"
        import time

        seconds = max(int(time.time() - state.checked_at), 0)
        if seconds < 60:
            return f"{seconds}s ago"
        if seconds < 3600:
            return f"{seconds // 60}m ago"
        return f"{seconds // 3600}h ago"

    def _update_summary(self, servers: list[Server]) -> None:
        summary = self.query_one("#summary", Static)
        server = next((entry for entry in servers if entry.id == self.selected_id), None)
        if server is None:
            summary.update(Text("No servers registered. Press A to add one.", style="bold cyan"))
            return
        state = self.app.states.get(server.id, ServerState(server=server))
        health = state.health
        lines = [
            Text.assemble((f"{server.name}", "bold cyan"), (f"  {server.ssh_target}:{server.port}", "dim")),
            Text(f"{state.status.symbol} {state.status.value}  ", style=STATUS_COLORS[state.status])
            + Text(status_reason(server, state.connectivity, health)),
        ]
        if health is not None:
            metrics = []
            if health.hostname:
                metrics.append(f"host {health.hostname}")
            if health.uptime_seconds is not None:
                metrics.append(f"uptime {_format_uptime(health.uptime_seconds)}")
            if health.load1 is not None:
                metrics.append(f"load {health.load1:.2f}")
            if health.mem_percent is not None:
                metrics.append(f"mem {health.mem_percent:.0f}%")
            if health.disk_percent is not None:
                metrics.append(f"disk {health.disk_percent:.0f}%")
            if health.temp_c is not None:
                metrics.append(f"temp {health.temp_c:.0f}C")
            if health.updates is not None:
                metrics.append(f"updates {health.updates}")
            if metrics:
                lines.append(Text("  ".join(metrics), style="dim"))
        summary.update(Text("\n").join(lines))

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        if event.row_key is None or event.row_key.value is None:
            return
        self.selected_id = str(event.row_key.value)
        self._update_summary(self.app.servers())

    def _selected_server(self) -> Server | None:
        if self.selected_id is None:
            return None
        return next((server for server in self.app.servers() if server.id == self.selected_id), None)

    def action_add_server(self) -> None:
        self.app.open_add_server()

    def action_edit_server(self) -> None:
        server = self._selected_server()
        if server is not None:
            self.app.open_edit_server(server)

    def action_remove_server(self) -> None:
        server = self._selected_server()
        if server is not None:
            self.app.open_remove_server(server)

    def action_ssh(self) -> None:
        server = self._selected_server()
        if server is not None:
            self.app.launch_ssh(server)

    def action_details(self) -> None:
        server = self._selected_server()
        if server is None:
            return
        from .detail import DetailScreen

        self.app.push_screen(DetailScreen(server, self.app.states.get(server.id)))

    def action_network(self) -> None:
        from .network import NetworkScreen

        self.app.push_screen(NetworkScreen())

    def action_troubleshoot(self) -> None:
        server = self._selected_server()
        if server is None:
            return
        state = self.app.states.get(server.id)
        reason = status_reason(server, state.connectivity, state.health) if state else "No health data."
        self.app.notify(
            f"{server.name}: {reason} (read-only V1; no remediation actions were taken)",
            title="Troubleshoot",
            severity="warning",
        )

    def action_refresh(self) -> None:
        self.app.refresh_states()

    def action_quit(self) -> None:
        self.app.exit()


def _format_uptime(seconds: int) -> str:
    days, remainder = divmod(max(int(seconds), 0), 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes = remainder // 60
    if days:
        return f"{days}d {hours:02d}h"
    if hours:
        return f"{hours}h {minutes:02d}m"
    return f"{minutes}m"
