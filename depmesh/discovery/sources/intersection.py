from __future__ import annotations

from depmesh.discovery.artifacts import EvaluationContext
from depmesh.discovery.sources.base import ArtifactSourceBase
from depmesh.discovery.sources.entities import IntersectionSourceConfig
from depmesh.domain.entities import ArtifactId


class IntersectionSource(ArtifactSourceBase):
    __slots__ = ("config", "items")

    def __init__(self, config: IntersectionSourceConfig, items: tuple[ArtifactSourceBase, ...]) -> None:
        self.config = config
        self.items = items

    def evaluate(self, context: EvaluationContext) -> list[ArtifactId]:
        artifact_sets = [set(item.evaluate(context)) for item in self.items]
        return sorted(set.intersection(*artifact_sets)) if artifact_sets else []


__all__ = ["IntersectionSource", "IntersectionSourceConfig"]
