import pytest

from kanslordash.models import Server, ValidationError


def test_server_defaults_and_target():
    server = Server(name=" LAS1 ", host=" 10.0.0.5 ", username="ops", tags="prod, web,prod")
    assert server.name == "LAS1"
    assert server.host == "10.0.0.5"
    assert server.ssh_target == "ops@10.0.0.5"
    assert server.address == "10.0.0.5:22"
    assert server.tags == ("prod", "web")
    assert server.id


@pytest.mark.parametrize(
    "payload",
    [
        {"name": "", "host": "10.0.0.5"},
        {"name": "x", "host": ""},
        {"name": "x", "host": "-oProxyCommand=bad"},
        {"name": "x", "host": "two words"},
        {"name": "x", "host": "host", "port": 0},
        {"name": "x", "host": "host", "port": 70000},
        {"name": "x", "host": "host", "port": "ssh"},
        {"name": "x", "host": "host", "os": "solaris"},
        {"name": "x", "host": "host", "username": "two words"},
        {"name": "x", "host": "host", "tags": "ok,bad,tag"},
    ],
)
def test_server_rejects_invalid_values(payload):
    with pytest.raises(ValidationError):
        Server(**payload)


def test_server_round_trip():
    server = Server(name="LAS1", host="10.0.0.5", os="linux", username="ops", port=2222, tags=("prod",))
    restored = Server.from_dict(server.to_dict())
    assert restored == server
