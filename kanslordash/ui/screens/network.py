from __future__ import annotations

import time

from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, DataTable, Static

from ...models import ServerState
from .dashboard import STATUS_COLORS


class NetworkScreen(ModalScreen[None]):
    BINDINGS = [Binding("escape", "close", "Close"), Binding("f5", "refresh", "Refresh")]

    def compose(self) -> ComposeResult:
        with Vertical(id="network"):
            yield Static("NETWORK // NODE CONNECTIVITY", classes="form-title")
            yield Static(id="network-summary")
            yield DataTable(id="network-table", cursor_type="row", zebra_stripes=True)
            yield Static(
                "Reachability uses the SSH TCP port with ICMP fallback. No Tailscale or VPN dependency.",
                classes="form-hint",
            )
            with Horizontal(classes="buttons"):
                yield Button("Refresh", variant="primary", id="refresh")
                yield Button("Close", id="close")

    def on_mount(self) -> None:
        table = self.query_one("#network-table", DataTable)
        table.add_columns("NODE", "ADDRESS", "PLATFORM", "STATE", "REACHABLE", "SSH", "LATENCY", "LAST RESPONSE")
        self._populate()

    def _populate(self) -> None:
        table = self.query_one("#network-table", DataTable)
        table.clear()
        states: dict[str, ServerState] = self.app.states
        servers = self.app.servers()
        online = degraded = offline = unknown = 0
        for server in servers:
            state = states.get(server.id)
            if state is None:
                unknown += 1
                status_text = Text("? UNKNOWN", style=STATUS_COLORS["UNKNOWN"])
                table.add_row(server.name, server.address, server.os, status_text, "unknown", "--", "--", "never")
                continue
            if state.status.value == "HEALTHY":
                online += 1
            elif state.status.value == "DEGRADED":
                degraded += 1
            elif state.status.value == "OFFLINE":
                offline += 1
            else:
                unknown += 1
            connectivity = state.connectivity
            reachable = "yes" if connectivity and connectivity.reachable else "no" if connectivity else "unknown"
            ssh_state = "open" if connectivity and connectivity.ssh_open else "closed" if connectivity else "unknown"
            latency = (
                f"{connectivity.latency_ms:.0f} ms"
                if connectivity and connectivity.latency_ms is not None
                else "icmp" if connectivity and connectivity.reachable else "--"
            )
            last = "never"
            if state.checked_at is not None:
                age = max(int(time.time() - state.checked_at), 0)
                last = f"{age}s ago" if age < 60 else f"{age // 60}m ago"
            table.add_row(
                server.name,
                server.address,
                server.os,
                Text(f"{state.status.symbol} {state.status.value}", style=STATUS_COLORS[state.status]),
                reachable,
                ssh_state,
                latency,
                last,
            )
        summary = self.query_one("#network-summary", Static)
        summary.update(
            Text(
                f"{len(servers)} nodes | {online} healthy | {degraded} degraded | "
                f"{offline} offline | {unknown} unknown"
            )
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "close":
            self.dismiss(None)
        elif event.button.id == "refresh":
            self.run_worker(self._refresh(), exclusive=True)

    async def _refresh(self) -> None:
        await self.app.collect_now()
        self._populate()

    def action_close(self) -> None:
        self.dismiss(None)

    def action_refresh(self) -> None:
        self.run_worker(self._refresh(), exclusive=True)
