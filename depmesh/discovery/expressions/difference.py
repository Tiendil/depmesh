from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from depmesh.core.entities import BaseEntity
from depmesh.discovery.expressions.entities import EvaluationContext
from depmesh.discovery.matchers import CaptureName
from depmesh.domain.entities import ArtifactId

if TYPE_CHECKING:
    from depmesh.discovery.expressions import DependencyExpression


class DifferenceExpression(BaseEntity):
    type: Literal["difference"]
    include: DependencyExpression
    exclude: DependencyExpression

    def variables(self) -> set[CaptureName]:
        return self.include.variables() | self.exclude.variables()

    def evaluate(self, context: EvaluationContext) -> list[ArtifactId]:
        return sorted(set(self.include.evaluate(context)) - set(self.exclude.evaluate(context)))
