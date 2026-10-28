from __future__ import annotations

from ..models import HealthSnapshot
from .base import Node


class UnknownNode(Node):
    async def health(self) -> HealthSnapshot:
        return HealthSnapshot(
            unknown=True,
            error="OS family is not configured; edit the server and select Linux or Windows.",
        )
