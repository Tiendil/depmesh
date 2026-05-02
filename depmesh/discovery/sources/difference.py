from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from depmesh.core.entities import BaseEntity
from depmesh.discovery.artifacts import CaptureName, EvaluationContext
from depmesh.domain.entities import ArtifactId

if TYPE_CHECKING:
    from depmesh.discovery.sources import ArtifactSource


class DifferenceSource(BaseEntity):
    type: Literal["difference"]
    include: ArtifactSource
    exclude: ArtifactSource

    def variables(self) -> set[CaptureName]:
        return self.include.variables() | self.exclude.variables()

    def evaluate(self, context: EvaluationContext) -> list[ArtifactId]:
        return sorted(set(self.include.evaluate(context)) - set(self.exclude.evaluate(context)))
