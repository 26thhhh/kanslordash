from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import platformdirs

APP_NAME = "kanslordash"
ENV_CONFIG_DIR = "KANSLORDASH_CONFIG_DIR"


@dataclass(slots=True)
class Settings:
    refresh_seconds: int = 60
    connect_timeout: float = 5.0
    health_timeout: float = 20.0
    max_concurrency: int = 4


def config_dir(override: str | Path | None = None) -> Path:
    if override:
        return Path(override)
    environment = os.environ.get(ENV_CONFIG_DIR)
    if environment:
        return Path(environment)
    return Path(platformdirs.user_config_dir(APP_NAME))


def registry_path(override: str | Path | None = None) -> Path:
    return config_dir(override) / "servers.json"


def log_dir() -> Path:
    return Path(platformdirs.user_log_dir(APP_NAME))


def ensure_private_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    try:
        path.chmod(0o700)
    except OSError:
        pass
