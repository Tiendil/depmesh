from __future__ import annotations

import glob
from pathlib import Path
from typing import Literal

from depmesh.core import warnings
from depmesh.discovery.artifacts import CaptureName, EvaluationContext, TemplateText
from depmesh.discovery.paths import normalize_existing_path, resolve_project_path
from depmesh.discovery.sources.base import ArtifactSourceBase
from depmesh.domain.entities import ArtifactId, UntrustedPath


class FilesSource(ArtifactSourceBase):
    type: Literal["files"]
    pattern: TemplateText | None = None

    def variables(self) -> set[CaptureName]:
        return set(self.pattern.variables) if self.pattern is not None else set()

    def evaluate(self, context: EvaluationContext) -> list[ArtifactId]:
        if self.pattern is None:
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

        pattern = self.pattern.substitute(context.captures)
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
