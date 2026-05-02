from __future__ import annotations

import glob
from pathlib import Path
from typing import Literal

from depmesh.core import warnings
from depmesh.core.entities import BaseEntity
from depmesh.discovery.artifacts import CaptureName, EvaluationContext, TemplateText
from depmesh.discovery.paths import normalize_existing_path, resolve_project_path
from depmesh.domain.entities import ArtifactId


class FilesSource(BaseEntity):
    type: Literal["files"]
    pattern: TemplateText | None = None

    def variables(self) -> set[CaptureName]:
        return set(self.pattern.variables) if self.pattern is not None else set()

    def evaluate(self, context: EvaluationContext) -> list[ArtifactId]:
        if self.pattern is None:
            return [
                ArtifactId(normalize_existing_path(path, context.root))
                for path in sorted(context.root.rglob("*"))
                if path.is_file()
            ]

        pattern = self.pattern.substitute(context.captures)
        resolved_pattern = resolve_project_path(pattern, context.root)

        if resolved_pattern is None:
            warnings.add(f"relation `{context.relation_id}`: skipped invalid files source pattern `{pattern}`")
            return []

        return [
            ArtifactId(normalize_existing_path(Path(match), context.root))
            for match in sorted(glob.glob(str(resolved_pattern), recursive=True))
            if Path(match).is_file()
        ]
