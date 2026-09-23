from __future__ import annotations

import importlib.resources
from pathlib import Path

from llm_tool_cli.config import create_config, resolve_config_path

from depmesh.workspace import errors
from depmesh.workspace.config import CONFIG_FILE_NAME

BASE_CONFIG_FIXTURE = "base_config.toml"


def initialize_config(path: Path | None = None, *, cwd: Path | None = None) -> Path:
    config_path = resolve_config_path(path or Path(CONFIG_FILE_NAME), cwd or Path.cwd())

    try:
        config_text = (
            importlib.resources.files(__package__)
            .joinpath("fixtures", BASE_CONFIG_FIXTURE)
            .read_text(encoding="utf-8")
        )
    except (OSError, UnicodeDecodeError) as error:
        raise errors.ConfigTemplateUnreadable(BASE_CONFIG_FIXTURE, str(error)) from error

    create_config(config_path, config_text)

    return config_path
