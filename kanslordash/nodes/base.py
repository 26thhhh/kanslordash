from __future__ import annotations

from abc import ABC, abstractmethod

from ..config import Settings
from ..models import Connectivity, HealthSnapshot, Server
from ..probes.network import probe_connectivity
from ..probes.ssh import build_interactive_ssh_argv


class Node(ABC):
    """Platform-specific view of one registered server.

    Every method is read-only. Interactive SSH is exposed as an argv vector so the
    UI can hand the terminal to the system ssh client.
    """

    def __init__(self, server: Server, settings: Settings) -> None:
        self.server = server
        self.settings = settings

    async def connectivity(self) -> Connectivity:
        return await probe_connectivity(self.server.host, self.server.port, self.settings.connect_timeout)

    @abstractmethod
    async def health(self) -> HealthSnapshot:
        raise NotImplementedError

    async def services(self) -> list[str]:
        return []

    async def updates(self) -> int | None:
        return None

    def ssh_argv(self) -> list[str]:
        return build_interactive_ssh_argv(self.server)
