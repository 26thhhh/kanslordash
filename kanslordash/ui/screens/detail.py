from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Static

from ...models import Server, ServerState
from ...status import status_reason
from .dashboard import _format_uptime


class DetailScreen(Screen[None]):
    BINDINGS = [Binding("escape", "close", "Close"), Binding("f5", "refresh", "Refresh")]

    def __init__(self, server: Server, state: ServerState | None) -> None:
        super().__init__()
        self.server = server
        self.initial_state = state

    def compose(self) -> ComposeResult:
        with Vertical(id="detail"):
            yield Static(f"{self.server.name} // SERVER DETAIL", classes="form-title")
            yield Static(self._build_text(), id="detail-body")
            with Horizontal(classes="buttons"):
                yield Button("Refresh", variant="primary", id="refresh")
                yield Button("Open SSH", id="ssh")
                yield Button("Close", id="close")

    def _state(self) -> ServerState | None:
        try:
            app_state = getattr(self.app, "states", {}) or {}
        except Exception:
            app_state = {}
        return app_state.get(self.server.id) or self.initial_state

    def _build_text(self) -> str:
        try:
            state = self._state()
            if state is None:
                return "No health data has been collected yet."
            health = state.health
            lines: list[str] = []
            lines.append(f"STATUS  {state.status.symbol} {state.status.value}")
            lines.append(f"REASON  {status_reason(self.server, state.connectivity, health)}")
            lines.append(f"TARGET  {self.server.ssh_target}:{self.server.port}")
            lines.append(f"PLATFORM {self.server.os}")
            lines.append(f"TAGS    {', '.join(self.server.tags) or '--'}")
            connectivity = state.connectivity
            if connectivity is not None:
                latency = f"{connectivity.latency_ms:.1f} ms" if connectivity.latency_ms is not None else "--"
                lines.append(f"NETWORK reachable={connectivity.reachable} ssh={connectivity.ssh_open} latency={latency}")
            if health is not None:
                lines.append("")
                lines.append("HEALTH")
                lines.append(f"Hostname         {health.hostname or '--'}")
                lines.append(f"Uptime           {_format_uptime(health.uptime_seconds) if health.uptime_seconds is not None else '--'}")
                if health.load1 is not None:
                    lines.append(f"Load (1m)        {health.load1:.2f}")
                else:
                    lines.append("Load (1m)        --")
                if health.cpu_percent is not None:
                    lines.append(f"CPU              {health.cpu_percent:.0f}%")
                else:
                    lines.append("CPU              --")
                if health.mem_percent is not None:
                    lines.append(f"Memory           {health.mem_percent:.0f}%")
                else:
                    lines.append("Memory           --")
                if health.disk_percent is not None:
                    lines.append(f"Disk             {health.disk_percent:.0f}%")
                else:
                    lines.append("Disk             --")
                if health.temp_c is not None:
                    lines.append(f"Temperature      {health.temp_c:.0f}C")
                else:
                    lines.append("Temperature      --")
                if health.failed_units is not None:
                    lines.append(f"Failed units     {health.failed_units}")
                else:
                    lines.append("Failed units     --")
                if health.updates is not None:
                    lines.append(f"Pending updates  {health.updates}")
                else:
                    lines.append("Pending updates  --")
                if health.error:
                    lines.append(f"Probe note: {health.error}")
            return "\n".join(lines)
        except Exception:
            return "Error rendering details."

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "close":
            self.app.pop_screen()
        elif event.button.id == "ssh":
            self.app.launch_ssh(self.server)
        elif event.button.id == "refresh":
            self.run_worker(self._refresh(), exclusive=True)

    async def _refresh(self) -> None:
        try:
            await self.app.collect_now()
        except Exception:
            pass
        try:
            body = self.query_one("#detail-body", Static)
            body.update(self._build_text())
        except Exception:
            pass

    def action_close(self) -> None:
        self.app.pop_screen()

    def action_refresh(self) -> None:
        self.run_worker(self._refresh(), exclusive=True)
