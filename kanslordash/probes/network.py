from __future__ import annotations

import asyncio
import os
import platform
import re

from ..models import Connectivity

_TIME_PATTERN = re.compile(r"time[=<]([0-9.]+)\s*ms")


async def _probe_tcp(host: str, port: int, timeout: float) -> tuple[bool, float | None, str | None]:
    loop = asyncio.get_running_loop()
    started = loop.time()
    try:
        reader, writer = await asyncio.wait_for(asyncio.open_connection(host, port), timeout=timeout)
    except asyncio.TimeoutError:
        return False, None, "connection timed out"
    except (OSError, ValueError) as error:
        return False, None, str(error)
    elapsed = (loop.time() - started) * 1000
    writer.close()
    try:
        await writer.wait_closed()
    except OSError:
        pass
    return True, round(elapsed, 1), None


async def _probe_icmp(host: str, timeout: float = 2.0) -> bool:
    if platform.system() == "Windows":
        argv = ["ping", "-n", "1", "-w", str(int(timeout * 1000)), host]
    else:
        argv = ["ping", "-n", "-c", "1", "-W", str(max(int(timeout), 1)), host]
    try:
        process = await asyncio.create_subprocess_exec(
            *argv,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
            env={**os.environ, "LC_ALL": "C"},
        )
        stdout, _ = await asyncio.wait_for(process.communicate(), timeout=timeout + 2)
    except (OSError, asyncio.TimeoutError):
        return False
    output = stdout.decode("utf-8", errors="replace")
    return process.returncode == 0 and bool(_TIME_PATTERN.search(output))


async def probe_connectivity(host: str, port: int, timeout: float) -> Connectivity:
    ssh_open, latency, error = await _probe_tcp(host, port, timeout)
    if ssh_open:
        return Connectivity(reachable=True, ssh_open=True, latency_ms=latency)
    icmp_ok = await _probe_icmp(host)
    if icmp_ok:
        return Connectivity(
            reachable=True,
            ssh_open=False,
            icmp_ok=True,
            error=error or "SSH port is not responding",
        )
    return Connectivity(reachable=False, ssh_open=False, icmp_ok=False, error=error or "host is unreachable")
