from __future__ import annotations

import importlib.resources
from pathlib import Path

from depmesh.workspace import errors
from depmesh.workspace.config import CONFIG_FILE_NAME

BASE_CONFIG_FIXTURE = "base_config.toml"


def initialize_config(path: Path | None = None, *, cwd: Path | None = None) -> Path:
    root = cwd or Path.cwd()
    config_path = path or root / CONFIG_FILE_NAME

    if not config_path.is_absolute():
        config_path = root / config_path

    config_path = config_path.resolve()

    if config_path.exists():
        raise errors.ConfigAlreadyExists(config_path)

    try:
        config_text = (
            importlib.resources.files(__package__)
            .joinpath("fixtures", BASE_CONFIG_FIXTURE)
            .read_text(encoding="utf-8")
        )
        config_path.write_text(config_text, encoding="utf-8")
    except OSError as error:
        raise errors.ConfigUnwritable(config_path, error) from error

    return config_path
