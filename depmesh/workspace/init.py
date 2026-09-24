from __future__ import annotations

import importlib.resources
from pathlib import Path

from llm_tool_cli.config import create_config, resolve_config_path
from llm_tool_cli.core.errors import EnvironmentErrors
from llm_tool_cli.core.result import Err, Ok, Result, unwrap_to_error

from depmesh.workspace import errors
from depmesh.workspace.config import CONFIG_FILE_NAME

BASE_CONFIG_FIXTURE = "base_config.toml"


@unwrap_to_error
def initialize_config(path: Path | None = None, *, cwd: Path | None = None) -> Result[Path, EnvironmentErrors]:
    config_path = resolve_config_path(path or Path(CONFIG_FILE_NAME), cwd or Path.cwd()).unwrap()

    try:
        config_text = (
            importlib.resources.files(__package__)
            .joinpath("fixtures", BASE_CONFIG_FIXTURE)
            .read_text(encoding="utf-8")
        )
    except (OSError, UnicodeDecodeError) as error:
        return Err(
            [errors.ConfigTemplateUnreadable(template=BASE_CONFIG_FIXTURE, reason=str(error)).with_cause(error)]
        )

    create_config(config_path, config_text).unwrap()

    return Ok(config_path)
