import json
import stat

import pytest

from kanslordash.models import Server, ValidationError
from kanslordash.registry import Registry, RegistryError


@pytest.fixture
def registry(tmp_path):
    instance = Registry(tmp_path / "servers.json")
    instance.load()
    return instance


def test_empty_registry(registry):
    assert registry.list() == []
    assert registry.get("missing") is None


def test_add_persists_and_sets_private_permissions(registry):
    server = registry.add(Server(name="LAS1", host="10.0.0.5"))
    assert registry.list() == [server]
    payload = json.loads(registry.path.read_text())
    assert payload["version"] == 1
    assert payload["servers"][0]["name"] == "LAS1"
    assert stat.S_IMODE(registry.path.stat().st_mode) == 0o600


def test_add_rejects_duplicate_name_and_address(registry):
    registry.add(Server(name="LAS1", host="10.0.0.5"))
    with pytest.raises(ValidationError, match="named"):
        registry.add(Server(name="las1", host="10.0.0.6"))
    with pytest.raises(ValidationError, match="already registered"):
        registry.add(Server(name="LAS2", host="10.0.0.5"))


def test_update_and_remove(registry):
    server = registry.add(Server(name="LAS1", host="10.0.0.5"))
    server.name = "LAS1-RENAMED"
    registry.update(server)
    assert registry.get("LAS1-RENAMED") is server
    removed = registry.remove(server.id)
    assert removed.id == server.id
    assert registry.list() == []


def test_reload_reads_persisted_servers(registry):
    registry.add(Server(name="LAS1", host="10.0.0.5"))
    reopened = Registry(registry.path)
    assert [server.name for server in reopened.load()] == ["LAS1"]


def test_corrupt_registry_raises(tmp_path):
    path = tmp_path / "servers.json"
    path.write_text("{not json")
    with pytest.raises(RegistryError):
        Registry(path).load()


def test_unsupported_schema_raises(tmp_path):
    path = tmp_path / "servers.json"
    path.write_text(json.dumps({"version": 99, "servers": []}))
    with pytest.raises(RegistryError):
        Registry(path).load()
