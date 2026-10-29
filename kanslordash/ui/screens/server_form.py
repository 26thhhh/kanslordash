from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
import os

from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Checkbox, Input, Label, Select, Static

from ...models import OS_CHOICES, Server, ValidationError


class AddServerScreen(ModalScreen[Server | None]):
    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("ctrl+s", "save", "Save"),
    ]

    def __init__(self, server: Server | None = None) -> None:
        super().__init__()
        self.existing = server

    def compose(self) -> ComposeResult:
        server = self.existing
        title = "EDIT SERVER" if server else "ADD SERVER"
        if os.name == "nt":
            key_placeholder = r"C:\Users\username\.ssh\id_ed25519"
        else:
            key_placeholder = "~/.ssh/id_ed25519"
        with Vertical(id="form"):
            yield Static(title, classes="form-title")
            yield Label("Display name")
            yield Input(value=server.name if server else "", placeholder="LAS1", id="name")
            yield Label("Hostname or IP address")
            yield Input(value=server.host if server else "", placeholder="192.168.1.10", id="host")
            yield Label("SSH username (optional)")
            yield Input(value=server.username if server else "", id="username")
            yield Label("SSH private key (optional)")
            yield Input(value=getattr(server, "ssh_key_path", "") if server else "", placeholder=key_placeholder, id="ssh_key_path")
            yield Label("Platform")
            yield Select(
                [(choice.capitalize(), choice) for choice in OS_CHOICES],
                value=server.os if server else "unknown",
                allow_blank=False,
                id="os",
            )
            yield Label("SSH port")
            yield Input(value=str(server.port) if server else "22", type="integer", id="port")
            yield Label("Tags (comma separated)")
            yield Input(value=",".join(server.tags) if server else "", id="tags")
            yield Checkbox("Enabled", value=server.enabled if server else True, id="enabled")
            yield Static(
                "Path to private key. Leave blank to use your normal SSH agent/config. Authentication uses your normal SSH agent/config. No passwords or keys are stored.",
                classes="form-hint",
            )
            with Horizontal(classes="buttons"):
                yield Button("Save", variant="primary", id="save")
                yield Button("Cancel", id="cancel")
            yield Static("Tab/Shift+Tab to move  |  Ctrl+S Save  |  Esc Cancel", classes="form-hint")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel":
            self.dismiss(None)
            return
        if event.button.id != "save":
            return
        self._submit()

    def action_save(self) -> None:
        self._submit()

    def _submit(self) -> None:
        try:
            os_value = self.query_one("#os", Select).value
            if os_value is None or os_value == Select.BLANK:
                raise ValidationError("Select a platform for the server.")
            values = {
                "name": self.query_one("#name", Input).value,
                "host": self.query_one("#host", Input).value,
                "os": str(os_value),
                "username": self.query_one("#username", Input).value,
                "ssh_key_path": self.query_one("#ssh_key_path", Input).value,
                "port": self.query_one("#port", Input).value or 22,
                "tags": self.query_one("#tags", Input).value,
                "enabled": self.query_one("#enabled", Checkbox).value,
            }
            if self.existing is not None:
                values["id"] = self.existing.id
                values["created_at"] = self.existing.created_at
            server = Server(**values)
        except ValidationError as error:
            self.app.notify(str(error), title="Invalid server", severity="error")
            return
        self.dismiss(server)

    def action_cancel(self) -> None:
        self.dismiss(None)


class ConfirmRemoveScreen(ModalScreen[bool]):
    BINDINGS = [Binding("escape", "cancel", "Cancel")]

    def __init__(self, server: Server) -> None:
        super().__init__()
        self.server = server

    def compose(self) -> ComposeResult:
        with Vertical(id="confirm"):
            yield Static("REMOVE SERVER", classes="form-title")
            yield Static(
                f"Remove {self.server.name} ({self.server.ssh_target}:{self.server.port}) from the registry?\n"
                "This only deletes the local registry entry; the server itself is not touched.",
                id="confirm-message",
            )
            with Horizontal(classes="buttons"):
                yield Button("Remove", variant="error", id="remove")
                yield Button("Cancel", id="cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "remove":
            self.dismiss(True)
        else:
            self.dismiss(False)

    def action_cancel(self) -> None:
        self.dismiss(False)
