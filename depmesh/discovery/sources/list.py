from __future__ import annotations

from llm_tool_cli.core.errors import EnvironmentErrors
from llm_tool_cli.core.result import Ok, Result, unwrap_to_error

from depmesh.discovery.artifacts import EvaluationContext
from depmesh.discovery.paths import normalize_path
from depmesh.discovery.sources.base import ArtifactSourceBase
from depmesh.discovery.sources.entities import ListSourceConfig
from depmesh.domain.entities import ArtifactId


class ListSource(ArtifactSourceBase):
    __slots__ = ("config",)

    def __init__(self, config: ListSourceConfig) -> None:
        self.config = config

    @unwrap_to_error
    def evaluate(self, context: EvaluationContext) -> Result[list[ArtifactId], EnvironmentErrors]:
        return Ok(
            sorted(
                {
                    ArtifactId(
                        normalize_path(
                            artifact.substitute(context.captures),
                            context.root,
                            cwd=context.cwd,
                        ).unwrap()
                    )
                    for artifact in self.config.artifacts
                }
            )
        )


__all__ = ["ListSource", "ListSourceConfig"]
