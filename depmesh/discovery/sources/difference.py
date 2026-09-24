from __future__ import annotations

from llm_tool_cli.core.errors import EnvironmentErrors
from llm_tool_cli.core.result import Ok, Result, unwrap_to_error

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

    @unwrap_to_error
    def evaluate(self, context: EvaluationContext) -> Result[list[ArtifactId], EnvironmentErrors]:
        included = set(self.include.evaluate(context).unwrap())
        excluded = set(self.exclude.evaluate(context).unwrap())
        return Ok(sorted(included - excluded))


__all__ = ["DifferenceSource", "DifferenceSourceConfig"]
