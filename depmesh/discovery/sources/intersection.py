from __future__ import annotations

from typing import TYPE_CHECKING, Literal

import pydantic

from depmesh.core.entities import BaseEntity
from depmesh.discovery.artifacts import CaptureName, EvaluationContext
from depmesh.domain.entities import ArtifactId

if TYPE_CHECKING:
    from depmesh.discovery.sources import ArtifactSource


class IntersectionSource(BaseEntity):
    type: Literal["intersection"]
    items: tuple[ArtifactSource, ...] = pydantic.Field(min_length=1)

    def variables(self) -> set[CaptureName]:
        return set().union(*(item.variables() for item in self.items))

    def evaluate(self, context: EvaluationContext) -> list[ArtifactId]:
        artifact_sets = [set(item.evaluate(context)) for item in self.items]
        return sorted(set.intersection(*artifact_sets)) if artifact_sets else []
