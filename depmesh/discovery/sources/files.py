from __future__ import annotations

from llm_tool_cli.core.result import Ok, Result, unwrap_to_error
from llm_tool_cli.paths import FileGlobPattern, enumerate_files
from llm_tool_cli.paths.errors import InvalidProjectPath

from depmesh.core import warnings
from depmesh.discovery.artifacts import EvaluationContext
from depmesh.discovery.sources.base import ArtifactSourceBase
from depmesh.discovery.sources.entities import FilesSourceConfig
from depmesh.domain.entities import ArtifactId


class FilesSource(ArtifactSourceBase):
    __slots__ = ("config",)

    def __init__(self, config: FilesSourceConfig) -> None:
        self.config = config

    @unwrap_to_error
    def evaluate(self, context: EvaluationContext) -> Result[list[ArtifactId]]:
        pattern = FileGlobPattern(
            self.config.pattern.substitute(context.captures) if self.config.pattern is not None else "**/*"
        )
        files = enumerate_files(context.root, pattern)
        if files.is_err(InvalidProjectPath):
            warnings.add(f"relation `{context.relation_id}`: skipped invalid files source pattern `{pattern}`")
            return Ok([])
        return Ok([ArtifactId(path) for path in files.unwrap()])


__all__ = ["FilesSource", "FilesSourceConfig"]
