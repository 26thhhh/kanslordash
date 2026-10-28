from __future__ import annotations

import json
import os
import stat
import tempfile
from pathlib import Path

from .config import ensure_private_dir
from .models import Server, ValidationError

SCHEMA_VERSION = 1


class RegistryError(RuntimeError):
    pass


class Registry:
    """Persistent, secret-free server registry backed by a JSON file."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self._servers: list[Server] = []
        self._loaded = False

    def load(self) -> list[Server]:
        if not self.path.exists():
            self._servers = []
            self._loaded = True
            return self.list()
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise RegistryError(f"Cannot read registry {self.path}: {error}") from error
        if not isinstance(payload, dict) or payload.get("version") != SCHEMA_VERSION:
            raise RegistryError(f"Unsupported registry format in {self.path}.")
        entries = payload.get("servers")
        if not isinstance(entries, list):
            raise RegistryError(f"Registry {self.path} has no server list.")
        try:
            self._servers = [Server.from_dict(entry) for entry in entries]
        except ValidationError as error:
            raise RegistryError(f"Invalid server entry in {self.path}: {error}") from error
        self._loaded = True
        return self.list()

    def list(self) -> list[Server]:
        self._ensure_loaded()
        return list(self._servers)

    def get(self, identifier: str) -> Server | None:
        self._ensure_loaded()
        needle = identifier.casefold()
        for server in self._servers:
            if server.id == identifier or server.name.casefold() == needle:
                return server
        return None

    def add(self, server: Server) -> Server:
        self._ensure_loaded()
        self._check_unique(server)
        self._servers.append(server)
        self._commit()
        return server

    def update(self, server: Server) -> Server:
        self._ensure_loaded()
        self._check_unique(server, ignore_id=server.id)
        for index, existing in enumerate(self._servers):
            if existing.id == server.id:
                self._servers[index] = server
                self._commit()
                return server
        raise RegistryError(f"Server {server.name!r} does not exist.")

    def remove(self, identifier: str) -> Server:
        self._ensure_loaded()
        server = self.get(identifier)
        if server is None:
            raise RegistryError(f"Server {identifier!r} does not exist.")
        self._servers = [entry for entry in self._servers if entry.id != server.id]
        self._commit()
        return server

    def _ensure_loaded(self) -> None:
        if not self._loaded:
            self.load()

    def _check_unique(self, server: Server, ignore_id: str | None = None) -> None:
        for existing in self._servers:
            if existing.id == ignore_id:
                continue
            if existing.name.casefold() == server.name.casefold():
                raise ValidationError(f"A server named {server.name!r} already exists.")
            if existing.address.casefold() == server.address.casefold():
                raise ValidationError(f"{server.address} is already registered.")

    def _commit(self) -> None:
        ensure_private_dir(self.path.parent)
        payload = {"version": SCHEMA_VERSION, "servers": [server.to_dict() for server in self._servers]}
        descriptor, temporary = tempfile.mkstemp(prefix=".servers-", suffix=".json", dir=self.path.parent)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, indent=2, sort_keys=True)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.chmod(temporary, stat.S_IRUSR | stat.S_IWUSR)
            os.replace(temporary, self.path)
        except OSError as error:
            raise RegistryError(f"Cannot save registry {self.path}: {error}") from error
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
