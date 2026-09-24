from __future__ import annotations

from llm_tool_cli.core.errors import EnvironmentErrors
from llm_tool_cli.core.result import Ok, Result, unwrap_to_error

from depmesh.discovery.artifacts import EvaluationContext
from depmesh.discovery.sources.base import ArtifactSourceBase
from depmesh.discovery.sources.entities import IntersectionSourceConfig
from depmesh.domain.entities import ArtifactId


class IntersectionSource(ArtifactSourceBase):
    __slots__ = ("config", "items")

    def __init__(self, config: IntersectionSourceConfig, items: tuple[ArtifactSourceBase, ...]) -> None:
        self.config = config
        self.items = items

    @unwrap_to_error
    def evaluate(self, context: EvaluationContext) -> Result[list[ArtifactId], EnvironmentErrors]:
        artifact_sets = [set(item.evaluate(context).unwrap()) for item in self.items]
        return Ok(sorted(set.intersection(*artifact_sets)) if artifact_sets else [])


__all__ = ["IntersectionSource", "IntersectionSourceConfig"]
