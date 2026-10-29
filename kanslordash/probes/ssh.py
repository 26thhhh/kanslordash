from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass

from ..models import Server

MAX_OUTPUT_BYTES = 256 * 1024


@dataclass(slots=True)
class SSHResult:
    ok: bool
    returncode: int | None = None
    stdout: str = ""
    stderr: str = ""
    timed_out: bool = False


def ssh_options(*, connect_timeout: float, batch: bool = True) -> list[str]:
    options = [
        "-o",
        f"ConnectTimeout={max(int(connect_timeout), 1)}",
        "-o",
        "LogLevel=ERROR",
    ]
    if batch:
        options += ["-o", "BatchMode=yes", "-o", "NumberOfPasswordPrompts=0"]
    return options


def build_ssh_argv(server: Server, remote_command: list[str], *, connect_timeout: float) -> list[str]:
    argv = [
        "ssh",
        "-T",
        "-p",
        str(server.port),
        *ssh_options(connect_timeout=connect_timeout, batch=True),
    ]
    key_path = getattr(server, "ssh_key_path", "") or ""
    if key_path:
        argv += ["-i", key_path]
    argv += [server.ssh_target, *remote_command]
    return argv


def build_interactive_ssh_argv(server: Server) -> list[str]:
    """Build a plain interactive SSH command; authentication follows the user's normal setup."""
    argv = ["ssh", "-p", str(server.port)]
    key_path = getattr(server, "ssh_key_path", "") or ""
    if key_path:
        argv += ["-i", key_path]
    argv += [server.ssh_target]
    return argv


async def run_ssh_script(
    server: Server,
    *,
    remote_command: list[str],
    script: str,
    timeout: float,
    connect_timeout: float,
) -> SSHResult:
    argv = build_ssh_argv(server, remote_command, connect_timeout=connect_timeout)
    try:
        process = await asyncio.create_subprocess_exec(
            *argv,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env={**os.environ, "LC_ALL": "C"},
        )
    except FileNotFoundError:
        return SSHResult(ok=False, stderr="ssh client is not installed")
    except OSError as error:
        return SSHResult(ok=False, stderr=f"cannot start ssh: {error}")

    try:
        stdout, stderr = await asyncio.wait_for(process.communicate(script.encode()), timeout=timeout)
    except asyncio.TimeoutError:
        process.kill()
        await process.wait()
        return SSHResult(ok=False, timed_out=True, stderr=f"probe timed out after {timeout:.0f}s")

    output = stdout[:MAX_OUTPUT_BYTES].decode("utf-8", errors="replace")
    error_output = stderr[:MAX_OUTPUT_BYTES].decode("utf-8", errors="replace").strip()
    return SSHResult(
        ok=process.returncode == 0,
        returncode=process.returncode,
        stdout=output,
        stderr=error_output,
    )
