from __future__ import annotations

from pathlib import Path

from llm_tool_cli.config import create_config_from_template, resolve_config_path
from llm_tool_cli.core.result import Ok, Result, unwrap_to_error
from llm_tool_cli.paths import ProjectConfigPath

from depmesh.workspace.config import CONFIG_FILE_NAME

BASE_CONFIG_FIXTURE = "base_config.toml"


@unwrap_to_error
def initialize_config(path: Path | None = None, *, cwd: Path | None = None) -> Result[ProjectConfigPath]:
    config_path = resolve_config_path(path or Path(CONFIG_FILE_NAME), cwd or Path.cwd()).unwrap()

    create_config_from_template(config_path, package=__package__, template=BASE_CONFIG_FIXTURE).unwrap()

    return Ok(config_path)
