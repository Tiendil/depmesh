from __future__ import annotations

from typing import Literal

from depmesh.core import warnings
from depmesh.core.entities import BaseEntity
from depmesh.discovery.expressions.entities import EvaluationContext, TemplateText
from depmesh.discovery.matchers import CaptureName
from depmesh.discovery.paths import normalize_existing_path, normalize_path, resolve_project_path
from depmesh.domain.entities import ArtifactId


class PathExpression(BaseEntity):
    type: Literal["path"]
    path: TemplateText

    def variables(self) -> set[CaptureName]:
        return set(self.path.variables)

    def evaluate(self, context: EvaluationContext) -> list[ArtifactId]:
        path_value = self.path.substitute(context.captures)
        path = resolve_project_path(path_value, context.root)

        if path is None:
            warnings.add(f"relation `{context.relation_id}`: skipped invalid dependency path `{path_value}`")
            return []

        if not path.is_file():
            warnings.add(
                f"relation `{context.relation_id}`: skipped missing dependency "
                f"`{normalize_path(path_value, context.root)}`"
            )
            return []

        return [ArtifactId(normalize_existing_path(path, context.root))]
