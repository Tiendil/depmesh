from __future__ import annotations

import glob
from pathlib import Path

from depmesh.core import warnings
from depmesh.discovery.artifacts import EvaluationContext
from depmesh.discovery.paths import normalize_existing_path, resolve_project_path
from depmesh.discovery.sources.base import ArtifactSourceBase
from depmesh.discovery.sources.entities import FilesSourceConfig
from depmesh.domain.entities import ArtifactId, UntrustedPath


class FilesSource(ArtifactSourceBase):
    __slots__ = ("config",)

    def __init__(self, config: FilesSourceConfig) -> None:
        self.config = config

    def evaluate(self, context: EvaluationContext) -> list[ArtifactId]:
        if self.config.pattern is None:
            return [
                ArtifactId(
                    normalize_existing_path(
                        UntrustedPath(path),
                        context.root,
                    )
                )
                for path in sorted(context.root.rglob("*"))
                if path.is_file()
            ]

        pattern = self.config.pattern.substitute(context.captures)
        resolved_pattern = resolve_project_path(pattern, context.root, allow_absolute=True)

        if resolved_pattern is None:
            warnings.add(f"relation `{context.relation_id}`: skipped invalid files source pattern `{pattern}`")
            return []

        return [
            ArtifactId(
                normalize_existing_path(
                    UntrustedPath(Path(match)),
                    context.root,
                )
            )
            for match in sorted(glob.glob(str(resolved_pattern), recursive=True))
            if Path(match).is_file()
        ]


__all__ = ["FilesSource", "FilesSourceConfig"]
