from __future__ import annotations

from ..models import HealthSnapshot
from ..probes.parsers import parse_windows_health
from ..probes.ssh import run_ssh_script
from .base import Node

WINDOWS_HEALTH_SCRIPT = r"""
$ErrorActionPreference = 'Stop'
$os = Get-CimInstance -ClassName Win32_OperatingSystem
$processor = Get-CimInstance -ClassName Win32_Processor | Measure-Object -Property LoadPercentage -Average
$disk = Get-CimInstance -ClassName Win32_LogicalDisk -Filter "DeviceID='$($env:SystemDrive)'"
$failed = @(Get-CimInstance -ClassName Win32_Service -Filter "StartMode='Auto'" | Where-Object { $_.State -ne 'Running' }).Count
$cpu = if ($null -ne $processor.Average) { [math]::Round($processor.Average) } else { $null }
$mem = if ($os.TotalVisibleMemorySize -gt 0) { [math]::Round((1 - ($os.FreePhysicalMemory / $os.TotalVisibleMemorySize)) * 100) } else { $null }
$diskUsed = if ($null -ne $disk -and $disk.Size -gt 0) { [math]::Round((1 - ($disk.FreeSpace / $disk.Size)) * 100) } else { $null }
$uptime = if ($null -ne $os.LastBootUpTime) { [int]((Get-Date) - $os.LastBootUpTime).TotalSeconds } else { $null }
[pscustomobject]@{
  hostname = $env:COMPUTERNAME
  os = 'windows'
  uptime_seconds = $uptime
  cpu_percent = $cpu
  mem_percent = $mem
  disk_percent = $diskUsed
  temp_c = $null
  failed_units = $failed
  updates = $null
} | ConvertTo-Json -Compress
"""

WINDOWS_SERVICES_SCRIPT = r"""
$ErrorActionPreference = 'Stop'
Get-CimInstance -ClassName Win32_Service -Filter "StartMode='Auto'" |
  Where-Object { $_.State -ne 'Running' } |
  Select-Object -ExpandProperty Name
"""


class WindowsNode(Node):
    async def health(self) -> HealthSnapshot:
        result = await run_ssh_script(
            self.server,
            remote_command=["powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", "-"],
            script=WINDOWS_HEALTH_SCRIPT,
            timeout=self.settings.health_timeout,
            connect_timeout=self.settings.connect_timeout,
        )
        if result.timed_out:
            return HealthSnapshot(os="windows", error=result.stderr or "Windows health probe timed out")
        if not result.ok:
            return HealthSnapshot(os="windows", error=result.stderr or "Windows health probe failed")
        snapshot = parse_windows_health(result.stdout)
        if snapshot.error and result.stderr:
            snapshot.error = f"{snapshot.error}: {result.stderr}"
        return snapshot

    async def services(self) -> list[str]:
        result = await run_ssh_script(
            self.server,
            remote_command=["powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", "-"],
            script=WINDOWS_SERVICES_SCRIPT,
            timeout=self.settings.health_timeout,
            connect_timeout=self.settings.connect_timeout,
        )
        if not result.ok:
            return []
        return [line.strip() for line in result.stdout.splitlines() if line.strip()]
