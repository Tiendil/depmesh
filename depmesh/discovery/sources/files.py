from __future__ import annotations

import glob
from pathlib import Path

from llm_tool_cli.core.errors import EnvironmentErrors
from llm_tool_cli.core.result import Err, Ok, Result, unwrap_to_error

from depmesh.core import warnings
from depmesh.discovery import errors
from depmesh.discovery.artifacts import EvaluationContext
from depmesh.discovery.paths import normalize_existing_path, resolve_project_path
from depmesh.discovery.sources.base import ArtifactSourceBase
from depmesh.discovery.sources.entities import FilesSourceConfig
from depmesh.domain.entities import ArtifactId, UntrustedPath


class FilesSource(ArtifactSourceBase):
    __slots__ = ("config",)

    def __init__(self, config: FilesSourceConfig) -> None:
        self.config = config

    @unwrap_to_error
    def evaluate(self, context: EvaluationContext) -> Result[list[ArtifactId], EnvironmentErrors]:
        try:
            if self.config.pattern is None:
                return Ok(
                    [
                        ArtifactId(
                            normalize_existing_path(
                                UntrustedPath(path),
                                context.root,
                            ).unwrap()
                        )
                        for path in sorted(context.root.rglob("*"))
                        if path.is_file()
                    ]
                )

            pattern = self.config.pattern.substitute(context.captures)
            resolved_pattern = resolve_project_path(pattern, context.root, allow_absolute=True).unwrap()

            if resolved_pattern is None:
                warnings.add(f"relation `{context.relation_id}`: skipped invalid files source pattern `{pattern}`")
                return Ok([])

            return Ok(
                [
                    ArtifactId(
                        normalize_existing_path(
                            UntrustedPath(Path(match)),
                            context.root,
                        ).unwrap()
                    )
                    for match in sorted(glob.glob(str(resolved_pattern), recursive=True))
                    if Path(match).is_file()
                ]
            )
        except OSError as error:
            return Err([errors.FilesUnreadable(path=str(context.root), reason=str(error)).with_cause(error)])


__all__ = ["FilesSource", "FilesSourceConfig"]
