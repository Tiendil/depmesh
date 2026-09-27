from __future__ import annotations

import glob
from pathlib import Path

from llm_tool_cli.core.result import Err, Ok, Result, unwrap_to_error
from llm_tool_cli.paths import project_path_id_from_filesystem, resolve_project_path
from llm_tool_cli.paths.errors import InvalidProjectPath

from depmesh.core import warnings
from depmesh.discovery import errors
from depmesh.discovery.artifacts import EvaluationContext
from depmesh.discovery.sources.base import ArtifactSourceBase
from depmesh.discovery.sources.entities import FilesSourceConfig
from depmesh.domain.entities import ArtifactId, UntrustedPath


class FilesSource(ArtifactSourceBase):
    __slots__ = ("config",)

    def __init__(self, config: FilesSourceConfig) -> None:
        self.config = config

    @unwrap_to_error
    def evaluate(self, context: EvaluationContext) -> Result[list[ArtifactId]]:
        try:
            if self.config.pattern is None:
                return Ok(
                    [
                        ArtifactId(
                            project_path_id_from_filesystem(
                                UntrustedPath(path),
                                context.root,
                            ).unwrap()
                        )
                        for path in sorted(context.root.rglob("*"))
                        if path.is_file()
                    ]
                )

            pattern = self.config.pattern.substitute(context.captures)
            resolved_pattern = resolve_project_path(pattern, context.root)

            if resolved_pattern.is_err(InvalidProjectPath):
                warnings.add(f"relation `{context.relation_id}`: skipped invalid files source pattern `{pattern}`")
                return Ok([])

            pattern_path = resolved_pattern.unwrap()
            return Ok(
                [
                    ArtifactId(
                        project_path_id_from_filesystem(
                            UntrustedPath(Path(match)),
                            context.root,
                        ).unwrap()
                    )
                    for match in sorted(glob.glob(str(pattern_path), recursive=True))
                    if Path(match).is_file()
                ]
            )
        except OSError as error:
            return Err([errors.FilesUnreadable(path=str(context.root), reason=str(error)).with_cause(error)])


__all__ = ["FilesSource", "FilesSourceConfig"]
