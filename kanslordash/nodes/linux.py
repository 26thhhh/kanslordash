from __future__ import annotations

from ..models import HealthSnapshot
from ..probes.parsers import parse_linux_health
from ..probes.ssh import run_ssh_script
from .base import Node

LINUX_HEALTH_SCRIPT = r"""
export LC_ALL=C
printf 'HOSTNAME=%s\n' "$(hostname 2>/dev/null)"
printf 'OS=linux\n'
UPTIME=$(cut -d. -f1 /proc/uptime 2>/dev/null)
printf 'UPTIME=%s\n' "${UPTIME:-}"
LOAD1=$(cut -d' ' -f1 /proc/loadavg 2>/dev/null)
printf 'LOAD1=%s\n' "$LOAD1"
MEM=$(awk '/^MemTotal:/{t=$2}/^MemAvailable:/{a=$2}END{if(t>0)printf "%.0f",(t-a)*100/t}' /proc/meminfo 2>/dev/null)
printf 'MEM=%s\n' "$MEM"
DISK=$(df -P / 2>/dev/null | awk 'NR==2{gsub("%","",$5);print $5}')
printf 'DISK=%s\n' "$DISK"
TEMP=""
if command -v vcgencmd >/dev/null 2>&1; then
  TEMP=$(vcgencmd measure_temp 2>/dev/null | sed -n 's/.*=\([0-9.]*\).*/\1/p')
fi
if [ -z "$TEMP" ]; then
  for ZONE in /sys/class/thermal/thermal_zone*/temp; do
    if [ -r "$ZONE" ]; then
      TEMP=$(awk '{printf "%.0f", $1/1000}' "$ZONE" 2>/dev/null)
      break
    fi
  done
fi
printf 'TEMP=%s\n' "$TEMP"
if command -v systemctl >/dev/null 2>&1; then
  FAILED=$(systemctl --failed --no-legend 2>/dev/null | wc -l)
  printf 'FAILED=%s\n' "$FAILED"
fi
"""

LINUX_UPDATES_SCRIPT = r"""
export LC_ALL=C
if command -v apt >/dev/null 2>&1; then
  apt list --upgradable 2>/dev/null | awk 'NR>1' | wc -l
fi
"""

LINUX_SERVICES_SCRIPT = r"""
export LC_ALL=C
if command -v systemctl >/dev/null 2>&1; then
  systemctl --failed --no-legend --plain 2>/dev/null | awk '{print $1}'
fi
"""


class LinuxNode(Node):
    async def health(self) -> HealthSnapshot:
        result = await run_ssh_script(
            self.server,
            remote_command=["sh", "-s"],
            script=LINUX_HEALTH_SCRIPT,
            timeout=self.settings.health_timeout,
            connect_timeout=self.settings.connect_timeout,
        )
        if result.timed_out:
            return HealthSnapshot(os="linux", error=result.stderr or "Linux health probe timed out")
        if not result.ok:
            return HealthSnapshot(os="linux", error=result.stderr or "Linux health probe failed")
        snapshot = parse_linux_health(result.stdout)
        if snapshot.error and result.stderr:
            snapshot.error = f"{snapshot.error}: {result.stderr}"
        return snapshot

    async def updates(self) -> int | None:
        result = await run_ssh_script(
            self.server,
            remote_command=["sh", "-s"],
            script=LINUX_UPDATES_SCRIPT,
            timeout=self.settings.health_timeout,
            connect_timeout=self.settings.connect_timeout,
        )
        if not result.ok:
            return None
        try:
            return int(result.stdout.strip().splitlines()[-1])
        except (ValueError, IndexError):
            return None

    async def services(self) -> list[str]:
        result = await run_ssh_script(
            self.server,
            remote_command=["sh", "-s"],
            script=LINUX_SERVICES_SCRIPT,
            timeout=self.settings.health_timeout,
            connect_timeout=self.settings.connect_timeout,
        )
        if not result.ok:
            return []
        return [line.strip() for line in result.stdout.splitlines() if line.strip()]
