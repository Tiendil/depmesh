from __future__ import annotations

from typing import TYPE_CHECKING, Literal

import pydantic

from depmesh.discovery.artifacts import CaptureName, EvaluationContext
from depmesh.discovery.sources.base import ArtifactSourceBase
from depmesh.domain.entities import ArtifactId

if TYPE_CHECKING:
    from depmesh.discovery.sources import ArtifactSource


class UnionSource(ArtifactSourceBase):
    type: Literal["union"]
    items: tuple[ArtifactSource, ...] = pydantic.Field(min_length=1)

    def variables(self) -> set[CaptureName]:
        return set().union(*(item.variables() for item in self.items))

    def evaluate(self, context: EvaluationContext) -> list[ArtifactId]:
        artifacts: set[ArtifactId] = set()

        for item in self.items:
            artifacts.update(item.evaluate(context))

        return sorted(artifacts)
