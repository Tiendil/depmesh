from __future__ import annotations

from llm_tool_cli.core.result import Ok, Result
from llm_tool_cli.paths import normalize_path
from llm_tool_cli.paths.errors import InvalidProjectPath

from depmesh.domain.entities import PathInput


def normalize_path_pattern(value: str, root: PathInput, *, cwd: PathInput | None = None) -> Result[str | None]:
    result = normalize_path(value, root, cwd=cwd)
    if result.is_err(InvalidProjectPath):
        return Ok(None)
    return result
