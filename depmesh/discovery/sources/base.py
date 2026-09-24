from __future__ import annotations

from llm_tool_cli.core.entities import BaseEntity
from llm_tool_cli.core.errors import EnvironmentErrors
from llm_tool_cli.core.result import Result

from depmesh.discovery.artifacts import CaptureName, EvaluationContext
from depmesh.domain.entities import ArtifactId


class ArtifactSourceConfigBase(BaseEntity):
    def variables(self) -> set[CaptureName]:
        return set()


class ArtifactSourceBase:
    def evaluate(self, context: EvaluationContext) -> Result[list[ArtifactId], EnvironmentErrors]:
        raise NotImplementedError
