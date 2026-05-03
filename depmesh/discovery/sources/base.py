from __future__ import annotations

from depmesh.core.entities import BaseEntity
from depmesh.discovery.artifacts import CaptureName, EvaluationContext
from depmesh.domain.entities import ArtifactId


class ArtifactSourceBase(BaseEntity):
    def variables(self) -> set[CaptureName]:
        return set()

    def evaluate(self, context: EvaluationContext) -> list[ArtifactId]:
        raise NotImplementedError
