from __future__ import annotations

import subprocess
from pathlib import Path

from textual import work
from textual.app import App
from textual.widgets import DataTable

from .config import Settings, registry_path
from .models import Server, ServerState, ValidationError
from .monitor import Monitor
from .nodes.base import Node
from .nodes.factory import build_node
from .probes.ssh import build_interactive_ssh_argv
from .registry import Registry, RegistryError
from .ui.screens.dashboard import DashboardScreen
from .ui.screens.detail import DetailScreen
from .ui.screens.network import NetworkScreen
from .ui.screens.server_form import AddServerScreen, ConfirmRemoveScreen


class KanslorDashApp(App):
    CSS_PATH = "ui/app.tcss"
    TITLE = "KanslorDash"

    def __init__(
        self,
        registry_file: str | Path | None = None,
        settings: Settings | None = None,
    ) -> None:
        super().__init__()
        self.settings = settings or Settings()
        self.registry = Registry(Path(registry_file) if registry_file else registry_path())
        self.monitor = Monitor(self.settings)
        self.states: dict[str, ServerState] = {}
        self.dashboard: DashboardScreen | None = None
        self.registry_error: str | None = None

    async def on_mount(self) -> None:
        try:
            self.registry.load()
        except RegistryError as error:
            self.registry_error = str(error)
            self.notify(str(error), title="Registry error", severity="error", timeout=10)
        screen = DashboardScreen()
        self.dashboard = screen
        await self.push_screen(screen)
        if self.settings.refresh_seconds > 0:
            self.set_interval(self.settings.refresh_seconds, self.refresh_states)
        self.refresh_states()

    def servers(self) -> list[Server]:
        if self.registry_error:
            return []
        try:
            return self.registry.list()
        except RegistryError as error:
            self.registry_error = str(error)
            return []

    async def collect_now(self) -> None:
        if self.registry_error:
            return
        servers = self.servers()
        results = await self.monitor.collect_all(servers)
        self.states = {state.server.id: state for state in results}
        if self.dashboard is not None and self.dashboard.is_mounted:
            self.dashboard.render_states(self.states, servers)

    @work(exclusive=True, group="refresh")
    async def refresh_states(self) -> None:
        try:
            await self.collect_now()
        except Exception as error:  # noqa: BLE001 - keep the dashboard alive
            self.notify(f"Refresh failed: {error}", title="Monitoring error", severity="error")

    def node_for(self, server: Server) -> Node:
        return build_node(server, self.settings)

    def open_add_server(self) -> None:
        self.push_screen(AddServerScreen(), self._added)

    def open_edit_server(self, server: Server) -> None:
        self.push_screen(AddServerScreen(server), lambda result: self._edited(server, result))

    def open_remove_server(self, server: Server) -> None:
        self.push_screen(
            ConfirmRemoveScreen(server),
            lambda confirmed: self._removed(server, bool(confirmed)),
        )

    def _added(self, server: Server | None) -> None:
        if server is None:
            return
        try:
            self.registry.add(server)
        except (ValidationError, RegistryError) as error:
            self.notify(str(error), title="Cannot add server", severity="error")
            return
        self.notify(f"Added {server.name}", title="Registry")
        self.refresh_states()

    def _edited(self, original: Server, updated: Server | None) -> None:
        if updated is None:
            return
        try:
            self.registry.update(updated)
        except (ValidationError, RegistryError) as error:
            self.notify(str(error), title="Cannot update server", severity="error")
            return
        self.states.pop(original.id, None)
        self.notify(f"Updated {updated.name}", title="Registry")
        self.refresh_states()

    def _removed(self, server: Server, confirmed: bool) -> None:
        if not confirmed:
            return
        try:
            self.registry.remove(server.id)
        except RegistryError as error:
            self.notify(str(error), title="Cannot remove server", severity="error")
            return
        self.states.pop(server.id, None)
        self.notify(f"Removed {server.name}", title="Registry")
        self.refresh_states()

    def launch_ssh(self, server: Server) -> None:
        argv = build_interactive_ssh_argv(server)
        try:
            with self.suspend():
                result = subprocess.run(argv, check=False)
        except FileNotFoundError:
            self.notify("ssh client is not installed", title="SSH", severity="error")
            return
        except OSError as error:
            self.notify(f"Cannot start ssh: {error}", title="SSH", severity="error")
            return
        if result.returncode:
            self.notify(f"SSH session exited with status {result.returncode}", title="SSH", severity="warning")
        self.refresh_states()

    def open_detail(self, server: Server) -> None:
        self.push_screen(DetailScreen(server, self.states.get(server.id)))

    def open_network(self) -> None:
        self.push_screen(NetworkScreen())

    def focus_table(self) -> None:
        if self.dashboard is not None and self.dashboard.is_mounted:
            self.dashboard.query_one("#servers", DataTable).focus()
