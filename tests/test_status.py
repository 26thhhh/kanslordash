from kanslordash.models import Connectivity, HealthSnapshot, HealthStatus, Server
from kanslordash.status import evaluate_status, status_reason


def make_server(enabled=True, os="linux"):
    return Server(name="x", host="10.0.0.5", os=os, enabled=enabled)


def test_disabled():
    server = make_server(enabled=False)
    assert evaluate_status(server, None, None) == HealthStatus.DISABLED


def test_never_checked_is_unknown_not_offline():
    server = make_server()
    assert evaluate_status(server, None, None) == HealthStatus.UNKNOWN
    assert "never" not in status_reason(server, None, None).lower() or status_reason(server, None, None)


def test_offline():
    server = make_server()
    conn = Connectivity(reachable=False, ssh_open=False, error="host is unreachable")
    assert evaluate_status(server, conn, None) == HealthStatus.OFFLINE


def test_reachable_but_no_ssh_degraded():
    server = make_server()
    conn = Connectivity(reachable=True, ssh_open=False, error="SSH port is not responding")
    assert evaluate_status(server, conn, None) == HealthStatus.DEGRADED


def test_healthy():
    server = make_server()
    conn = Connectivity(reachable=True, ssh_open=True, latency_ms=24)
    health = HealthSnapshot(cpu_percent=14, mem_percent=38, disk_percent=42)
    assert evaluate_status(server, conn, health) == HealthStatus.HEALTHY


def test_degraded_on_failed_units():
    server = make_server()
    conn = Connectivity(reachable=True, ssh_open=True)
    health = HealthSnapshot(failed_units=2)
    assert evaluate_status(server, conn, health) == HealthStatus.DEGRADED


def test_degraded_on_memory_threshold():
    server = make_server()
    conn = Connectivity(reachable=True, ssh_open=True)
    health = HealthSnapshot(mem_percent=90)
    assert evaluate_status(server, conn, health) == HealthStatus.DEGRADED


def test_unknown_when_os_unconfigured():
    server = make_server(os="unknown")
    conn = Connectivity(reachable=True, ssh_open=True)
    health = HealthSnapshot(unknown=True, error="OS family is not configured; edit the server and select Linux or Windows.")
    assert evaluate_status(server, conn, health) == HealthStatus.UNKNOWN
