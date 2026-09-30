from __future__ import annotations

from pathlib import Path

from llm_tool_cli.config import create_config_from_template, resolve_init_config_path
from llm_tool_cli.core.result import Ok, Result, unwrap_to_error
from llm_tool_cli.paths import PathInput, ProjectConfigPath

from depmesh.workspace.config import CONFIG_FILE_NAME

BASE_CONFIG_FIXTURE = "base_config.toml"


@unwrap_to_error
def initialize_config(path: ProjectConfigPath | None = None, *, cwd: Path | None = None) -> Result[ProjectConfigPath]:
    config_path = resolve_init_config_path(CONFIG_FILE_NAME, path=path, cwd=PathInput(cwd or Path.cwd())).unwrap()

    create_config_from_template(config_path, package=__package__, template=BASE_CONFIG_FIXTURE).unwrap()

    return Ok(config_path)
