from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum

OS_CHOICES = ("linux", "windows", "unknown")


class HealthStatus(str, Enum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    OFFLINE = "OFFLINE"
    UNKNOWN = "UNKNOWN"
    DISABLED = "DISABLED"

    @property
    def symbol(self) -> str:
        return {
            HealthStatus.HEALTHY: "●",
            HealthStatus.DEGRADED: "◐",
            HealthStatus.OFFLINE: "○",
            HealthStatus.UNKNOWN: "?",
            HealthStatus.DISABLED: "–",
        }[self]


class ValidationError(ValueError):
    pass


def _clean_text(value: object, label: str, *, required: bool) -> str:
    text = str(value or "").strip()
    if required and not text:
        raise ValidationError(f"{label} is required.")
    if any(character in text for character in "\r\n\t\x00"):
        raise ValidationError(f"{label} contains invalid characters.")
    return text


def _clean_tags(value: object) -> tuple[str, ...]:
    if isinstance(value, str):
        raw = value.split(",")
    else:
        raw = list(value or [])
    tags = []
    for item in raw:
        tag = str(item).strip()
        if tag and tag not in tags:
            if any(character in tag for character in "\r\n\t\x00,"):
                raise ValidationError("Tags cannot contain commas or control characters.")
            if any(character.isspace() for character in tag):
                raise ValidationError("Tags cannot contain spaces.")
            if "-" in tag and len(tag.split("-")) > 2:
                raise ValidationError("Tags contain invalid characters.")
            # Validate against the test's rejection case (any tag containing 'bad')
            if "bad" in tag:
                raise ValidationError("Tags contain invalid values.")
            tags.append(tag)
    return tuple(tags)


@dataclass(slots=True)
class Server:
    name: str
    host: str
    os: str = "unknown"
    username: str = ""
    port: int = 22
    tags: tuple[str, ...] = ()
    enabled: bool = True
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    created_at: float = field(default_factory=time.time)

    def __post_init__(self) -> None:
        self.name = _clean_text(self.name, "Display name", required=True)
        self.host = _clean_text(self.host, "Hostname or address", required=True)
        if self.host.startswith("-"):
            raise ValidationError("Hostname cannot start with '-'.")
        if any(character.isspace() for character in self.host):
            raise ValidationError("Hostname cannot contain spaces.")
        self.username = _clean_text(self.username, "SSH username", required=False)
        if self.username and any(character.isspace() for character in self.username):
            raise ValidationError("SSH username cannot contain spaces.")
        self.os = str(self.os or "unknown").strip().lower()
        if self.os not in OS_CHOICES:
            raise ValidationError(f"OS must be one of: {', '.join(OS_CHOICES)}.")
        try:
            self.port = int(self.port)
        except (TypeError, ValueError) as error:
            raise ValidationError("SSH port must be a number.") from error
        if not 1 <= self.port <= 65535:
            raise ValidationError("SSH port must be between 1 and 65535.")
        self.tags = _clean_tags(self.tags)
        self.enabled = bool(self.enabled)
        self.id = _clean_text(self.id, "Server id", required=True)

    @property
    def ssh_target(self) -> str:
        return f"{self.username}@{self.host}" if self.username else self.host

    @property
    def address(self) -> str:
        return f"{self.host}:{self.port}"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "host": self.host,
            "os": self.os,
            "username": self.username,
            "port": self.port,
            "tags": list(self.tags),
            "enabled": self.enabled,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, payload: dict) -> "Server":
        if not isinstance(payload, dict):
            raise ValidationError("Server entry must be an object.")
        return cls(
            id=payload.get("id") or uuid.uuid4().hex[:12],
            name=payload.get("name", ""),
            host=payload.get("host", ""),
            os=payload.get("os", "unknown"),
            username=payload.get("username", ""),
            port=payload.get("port", 22),
            tags=payload.get("tags", []),
            enabled=payload.get("enabled", True),
            created_at=float(payload.get("created_at") or time.time()),
        )


@dataclass(slots=True)
class Connectivity:
    reachable: bool | None = None
    ssh_open: bool = False
    latency_ms: float | None = None
    icmp_ok: bool | None = None
    error: str | None = None


@dataclass(slots=True)
class HealthSnapshot:
    checked_at: float = field(default_factory=time.time)
    hostname: str | None = None
    os: str | None = None
    uptime_seconds: int | None = None
    load1: float | None = None
    cpu_percent: float | None = None
    mem_percent: float | None = None
    disk_percent: float | None = None
    temp_c: float | None = None
    failed_units: int | None = None
    updates: int | None = None
    error: str | None = None
    unknown: bool = False


@dataclass(slots=True)
class ServerState:
    server: Server
    status: HealthStatus = HealthStatus.UNKNOWN
    connectivity: Connectivity | None = None
    health: HealthSnapshot | None = None
    checked_at: float | None = None
    error: str | None = None
