from __future__ import annotations

import glob
from pathlib import Path
from typing import Literal

from depmesh.core import warnings
from depmesh.core.entities import BaseEntity
from depmesh.discovery.expressions.entities import EvaluationContext, TemplateText
from depmesh.discovery.matchers import CaptureName
from depmesh.discovery.paths import normalize_existing_path, resolve_project_path
from depmesh.domain.entities import ArtifactId


class GlobExpression(BaseEntity):
    type: Literal["glob"]
    pattern: TemplateText

    def variables(self) -> set[CaptureName]:
        return set(self.pattern.variables)

    def evaluate(self, context: EvaluationContext) -> list[ArtifactId]:
        pattern = self.pattern.substitute(context.captures)
        resolved_pattern = resolve_project_path(pattern, context.root)

        if resolved_pattern is None:
            warnings.add(f"relation `{context.relation_id}`: skipped invalid dependency glob `{pattern}`")
            return []

        absolute_pattern = str(resolved_pattern)

        return [
            ArtifactId(normalize_existing_path(Path(match), context.root))
            for match in sorted(glob.glob(absolute_pattern, recursive=True))
            if Path(match).is_file()
        ]
