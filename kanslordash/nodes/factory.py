from __future__ import annotations

from ..config import Settings
from ..models import Server
from .base import Node
from .linux import LinuxNode
from .unknown import UnknownNode
from .windows import WindowsNode


def build_node(server: Server, settings: Settings) -> Node:
    if server.os == "linux":
        return LinuxNode(server, settings)
    if server.os == "windows":
        return WindowsNode(server, settings)
    return UnknownNode(server, settings)
