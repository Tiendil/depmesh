from __future__ import annotations

from depmesh.discovery.artifacts import EvaluationContext
from depmesh.discovery.sources.base import ArtifactSourceBase
from depmesh.discovery.sources.entities import UnionSourceConfig
from depmesh.domain.entities import ArtifactId


class UnionSource(ArtifactSourceBase):
    __slots__ = ("config", "items")

    def __init__(self, config: UnionSourceConfig, items: tuple[ArtifactSourceBase, ...]) -> None:
        self.config = config
        self.items = items

    def evaluate(self, context: EvaluationContext) -> list[ArtifactId]:
        artifacts: set[ArtifactId] = set()

        for item in self.items:
            artifacts.update(item.evaluate(context))

        return sorted(artifacts)


__all__ = ["UnionSource", "UnionSourceConfig"]
