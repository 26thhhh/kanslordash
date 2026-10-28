from __future__ import annotations

import asyncio
import time

from .config import Settings
from .models import HealthStatus, Server, ServerState
from .nodes import build_node
from .status import evaluate_status


class Monitor:
    """Read-only health collection with bounded concurrency."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings()
        self._semaphore = asyncio.Semaphore(self.settings.max_concurrency)

    async def collect(self, server: Server) -> ServerState:
        async with self._semaphore:
            return await self._collect(server)

    async def _collect(self, server: Server) -> ServerState:
        state = ServerState(server=server)
        if not server.enabled:
            state.status = HealthStatus.DISABLED
            state.checked_at = time.time()
            return state

        node = build_node(server, self.settings)
        try:
            state.connectivity = await node.connectivity()
        except Exception as error:  # noqa: BLE001 - a probe must never crash the dashboard
            state.error = f"connectivity probe failed: {error}"
            state.status = HealthStatus.UNKNOWN
            state.checked_at = time.time()
            return state

        if state.connectivity.ssh_open:
            try:
                state.health = await node.health()
            except Exception as error:  # noqa: BLE001
                state.error = f"health probe failed: {error}"

        state.status = evaluate_status(server, state.connectivity, state.health)
        state.checked_at = time.time()
        return state

    async def collect_all(self, servers: list[Server]) -> list[ServerState]:
        if not servers:
            return []
        return list(await asyncio.gather(*(self.collect(server) for server in servers)))
