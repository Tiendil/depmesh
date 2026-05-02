from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from depmesh.core.entities import BaseEntity
from depmesh.discovery.artifacts import CaptureName, EvaluationContext
from depmesh.discovery.predicates import ArtifactPredicate
from depmesh.domain.entities import ArtifactId

if TYPE_CHECKING:
    from depmesh.discovery.sources import ArtifactSource


class FilterSource(BaseEntity):
    type: Literal["filter"]
    source: ArtifactSource
    predicate: ArtifactPredicate

    def variables(self) -> set[CaptureName]:
        return self.source.variables() | self.predicate.variables()

    def evaluate(self, context: EvaluationContext) -> list[ArtifactId]:
        return [
            artifact
            for artifact in self.source.evaluate(context)
            if self.predicate.match(artifact, context.root, context.captures) is not None
        ]
