from __future__ import annotations

from llm_tool_cli.core.errors import EnvironmentErrors
from llm_tool_cli.core.result import Ok, Result, unwrap_to_error

from depmesh.discovery.artifacts import EvaluationContext
from depmesh.discovery.sources.base import ArtifactSourceBase
from depmesh.discovery.sources.entities import UnionSourceConfig
from depmesh.domain.entities import ArtifactId


class UnionSource(ArtifactSourceBase):
    __slots__ = ("config", "items")

    def __init__(self, config: UnionSourceConfig, items: tuple[ArtifactSourceBase, ...]) -> None:
        self.config = config
        self.items = items

    @unwrap_to_error
    def evaluate(self, context: EvaluationContext) -> Result[list[ArtifactId], EnvironmentErrors]:
        artifacts: set[ArtifactId] = set()

        for item in self.items:
            artifacts.update(item.evaluate(context).unwrap())

        return Ok(sorted(artifacts))


__all__ = ["UnionSource", "UnionSourceConfig"]
