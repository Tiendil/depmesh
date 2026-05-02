from __future__ import annotations

from typing import Literal

import pydantic

from depmesh.core.entities import BaseEntity
from depmesh.discovery.artifacts import CaptureName, EvaluationContext, TemplateText
from depmesh.discovery.paths import normalize_path
from depmesh.domain.entities import ArtifactId


class ListSource(BaseEntity):
    type: Literal["list"]
    artifacts: tuple[TemplateText, ...] = pydantic.Field(min_length=1)

    def variables(self) -> set[CaptureName]:
        return set().union(*(artifact.variables for artifact in self.artifacts))

    def evaluate(self, context: EvaluationContext) -> list[ArtifactId]:
        return sorted(
            {
                ArtifactId(normalize_path(artifact.substitute(context.captures), context.root, cwd=context.cwd))
                for artifact in self.artifacts
            }
        )
