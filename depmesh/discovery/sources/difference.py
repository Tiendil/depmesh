from __future__ import annotations

from depmesh.discovery.artifacts import EvaluationContext
from depmesh.discovery.sources.base import ArtifactSourceBase
from depmesh.discovery.sources.entities import DifferenceSourceConfig
from depmesh.domain.entities import ArtifactId


class DifferenceSource(ArtifactSourceBase):
    __slots__ = ("config", "exclude", "include")

    def __init__(
        self,
        config: DifferenceSourceConfig,
        *,
        include: ArtifactSourceBase,
        exclude: ArtifactSourceBase,
    ) -> None:
        self.config = config
        self.include = include
        self.exclude = exclude

    def evaluate(self, context: EvaluationContext) -> list[ArtifactId]:
        included = set(self.include.evaluate(context))
        excluded = set(self.exclude.evaluate(context))
        return sorted(included - excluded)


__all__ = ["DifferenceSource", "DifferenceSourceConfig"]
