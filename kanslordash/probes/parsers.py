from __future__ import annotations

import json
import re
from typing import Any

from ..models import HealthSnapshot, ValidationError

_NUMBER = re.compile(r"-?[0-9]+(?:\.[0-9]+)?")


def _number(value: Any) -> float | None:
    if value is None:
        return None
    match = _NUMBER.search(str(value))
    return float(match.group(0)) if match else None


def _integer(value: Any) -> int | None:
    number = _number(value)
    return int(number) if number is not None else None


def parse_linux_health(output: str) -> HealthSnapshot:
    fields: dict[str, str] = {}
    for line in output.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            fields[key.strip().upper()] = value.strip()

    if not fields:
        return HealthSnapshot(os="linux", error="Linux health probe returned no data")

    snapshot = HealthSnapshot(
        hostname=fields.get("HOSTNAME") or None,
        os="linux",
        uptime_seconds=_integer(fields.get("UPTIME")),
        load1=_number(fields.get("LOAD1")),
        cpu_percent=_number(fields.get("CPU")),
        mem_percent=_number(fields.get("MEM")),
        disk_percent=_number(fields.get("DISK")),
        temp_c=_number(fields.get("TEMP")),
        failed_units=_integer(fields.get("FAILED")),
        updates=_integer(fields.get("UPDATES")),
    )
    if all(
        value is None
        for value in (
            snapshot.uptime_seconds,
            snapshot.load1,
            snapshot.mem_percent,
            snapshot.disk_percent,
            snapshot.failed_units,
        )
    ):
        snapshot.error = "Linux health probe returned no usable metrics"
    return snapshot


def parse_windows_health(output: str) -> HealthSnapshot:
    payload = _extract_json_object(output)
    if payload is None:
        return HealthSnapshot(os="windows", error="Windows health probe returned no data")

    try:
        data = json.loads(payload)
    except json.JSONDecodeError as error:
        return HealthSnapshot(os="windows", error=f"Windows health probe returned invalid JSON: {error}")
    if isinstance(data, list):
        data = data[0] if data else {}
    if not isinstance(data, dict):
        raise ValidationError("Windows health probe returned an unexpected payload")

    snapshot = HealthSnapshot(
        hostname=str(data.get("hostname") or "") or None,
        os="windows",
        uptime_seconds=_integer(data.get("uptime_seconds")),
        load1=_number(data.get("load1")),
        cpu_percent=_number(data.get("cpu_percent")),
        mem_percent=_number(data.get("mem_percent")),
        disk_percent=_number(data.get("disk_percent")),
        temp_c=_number(data.get("temp_c")),
        failed_units=_integer(data.get("failed_units")),
        updates=_integer(data.get("updates")),
    )
    if all(
        value is None
        for value in (
            snapshot.uptime_seconds,
            snapshot.cpu_percent,
            snapshot.mem_percent,
            snapshot.disk_percent,
            snapshot.failed_units,
        )
    ):
        snapshot.error = "Windows health probe returned no usable metrics"
    return snapshot


def _extract_json_object(output: str) -> str | None:
    text = output.strip()
    if not text:
        return None
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    return text[start : end + 1]
