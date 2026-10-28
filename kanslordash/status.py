from __future__ import annotations

from .models import Connectivity, HealthSnapshot, HealthStatus, Server

TEMP_WARNING = 70.0
TEMP_CRITICAL = 80.0
MEMORY_WARNING = 85.0
MEMORY_CRITICAL = 95.0
DISK_WARNING = 85.0
DISK_CRITICAL = 95.0


def evaluate_status(
    server: Server,
    connectivity: Connectivity | None,
    health: HealthSnapshot | None,
) -> HealthStatus:
    if not server.enabled:
        return HealthStatus.DISABLED
    if connectivity is None or connectivity.reachable is None:
        return HealthStatus.UNKNOWN
    if not connectivity.reachable:
        return HealthStatus.OFFLINE
    if not connectivity.ssh_open:
        return HealthStatus.DEGRADED
    if health is None:
        return HealthStatus.DEGRADED
    if health.unknown:
        return HealthStatus.UNKNOWN
    if health.error:
        return HealthStatus.DEGRADED
    if _health_degraded(health):
        return HealthStatus.DEGRADED
    return HealthStatus.HEALTHY


def _health_degraded(health: HealthSnapshot) -> bool:
    if health.failed_units is not None and health.failed_units > 0:
        return True
    for value, warning in (
        (health.temp_c, TEMP_WARNING),
        (health.mem_percent, MEMORY_WARNING),
        (health.disk_percent, DISK_WARNING),
        (health.cpu_percent, 95.0),
    ):
        if value is not None and value >= warning:
            return True
    return False


def status_reason(
    server: Server,
    connectivity: Connectivity | None,
    health: HealthSnapshot | None,
) -> str:
    status = evaluate_status(server, connectivity, health)
    if status is HealthStatus.DISABLED:
        return "Server is disabled in the registry."
    if status is HealthStatus.OFFLINE:
        return connectivity.error if connectivity and connectivity.error else "Host is unreachable."
    if status is HealthStatus.UNKNOWN:
        if health is not None and health.unknown:
            return health.error or "Health data is unavailable."
        return "No health check has completed yet."
    if connectivity is not None and not connectivity.ssh_open:
        return connectivity.error or "Host responds, but the SSH port is closed."
    if health is not None and health.error:
        return health.error
    warnings = []
    if health is not None:
        if health.failed_units:
            warnings.append(f"{health.failed_units} failed unit(s)")
        if health.temp_c is not None and health.temp_c >= TEMP_WARNING:
            warnings.append(f"temperature {health.temp_c:.0f}C")
        if health.mem_percent is not None and health.mem_percent >= MEMORY_WARNING:
            warnings.append(f"memory {health.mem_percent:.0f}%")
        if health.disk_percent is not None and health.disk_percent >= DISK_WARNING:
            warnings.append(f"disk {health.disk_percent:.0f}%")
    if warnings:
        return ", ".join(warnings)
    return "All collected metrics are within thresholds."
