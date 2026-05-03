from __future__ import annotations

from depmesh.discovery.artifacts import EvaluationContext
from depmesh.discovery.predicates.base import ArtifactPredicateBase
from depmesh.discovery.sources.base import ArtifactSourceBase
from depmesh.discovery.sources.entities import FilterSourceConfig
from depmesh.domain.entities import ArtifactId


class FilterSource(ArtifactSourceBase):
    __slots__ = ("config", "predicate", "source")

    def __init__(
        self,
        config: FilterSourceConfig,
        source: ArtifactSourceBase,
        predicate: ArtifactPredicateBase,
    ) -> None:
        self.config = config
        self.source = source
        self.predicate = predicate

    def evaluate(self, context: EvaluationContext) -> list[ArtifactId]:
        return [
            artifact
            for artifact in self.source.evaluate(context)
            if self.predicate.match(artifact, context.root, context.captures) is not None
        ]


__all__ = ["FilterSource", "FilterSourceConfig"]
