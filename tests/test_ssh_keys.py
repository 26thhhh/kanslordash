import os
import sys

import pytest

from kanslordash.models import Server, ValidationError
from kanslordash.probes import ssh


def test_server_backward_compatible_without_ssh_key_path():
    server = Server(name="s1", host="10.0.0.1")
    assert server.ssh_key_path == ""
    d = server.to_dict()
    assert "ssh_key_path" in d


def test_server_persists_ssh_key_path(tmp_path):
    key = tmp_path / "id_ed25519"
    key.write_text("fake")
    os.chmod(key, 0o600)
    server = Server(name="s1", host="10.0.0.1", ssh_key_path=str(key))
    d = server.to_dict()
    restored = Server.from_dict(d)
    assert restored.ssh_key_path == os.path.expandvars(os.path.expanduser(str(key)))


def test_ssh_key_path_rejects_pub():
    with pytest.raises(ValidationError):
        Server(name="s1", host="10.0.0.1", ssh_key_path="/tmp/key.pub")


def test_ssh_key_path_rejects_directory(tmp_path):
    with pytest.raises(ValidationError):
        Server(name="s1", host="10.0.0.1", ssh_key_path=str(tmp_path))


def test_ssh_key_path_with_spaces(tmp_path):
    d = tmp_path / "my keys"
    d.mkdir()
    key = d / "id_rsa"
    key.write_text("fake")
    server = Server(name="s1", host="10.0.0.1", ssh_key_path=str(key))
    assert server.ssh_key_path


def test_ssh_key_path_expands_tilde(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    key = tmp_path / "id_ed25519"
    key.write_text("fake")
    server = Server(name="s1", host="10.0.0.1", ssh_key_path="~/id_ed25519")
    assert server.ssh_key_path.endswith("id_ed25519")


def test_build_ssh_argv_with_key(tmp_path):
    key = tmp_path / "id_ed25519"
    key.write_text("fake")
    server = Server(name="s1", host="10.0.0.1", username="ops", ssh_key_path=str(key))
    argv = ssh.build_ssh_argv(server, ["echo", "hi"], connect_timeout=5)
    assert "-i" in argv
    idx = argv.index("-i")
    assert argv[idx + 1] == server.ssh_key_path


def test_build_interactive_ssh_argv_with_key(tmp_path):
    key = tmp_path / "id_ed25519"
    key.write_text("fake")
    server = Server(name="s1", host="10.0.0.1", ssh_key_path=str(key))
    argv = ssh.build_interactive_ssh_argv(server)
    assert "-i" in argv


def test_build_ssh_argv_without_key():
    server = Server(name="s1", host="10.0.0.1")
    argv = ssh.build_ssh_argv(server, ["echo", "hi"], connect_timeout=5)
    assert "-i" not in argv


def test_existing_config_without_key_compatible():
    payload = {"id": "abc", "name": "s1", "host": "10.0.0.1", "os": "linux", "username": "", "port": 22, "tags": [], "enabled": True, "created_at": 123.0}
    server = Server.from_dict(payload)
    assert server.ssh_key_path == ""
