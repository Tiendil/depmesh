from __future__ import annotations

from typing import TYPE_CHECKING, Literal

import pydantic

from depmesh.core.entities import BaseEntity
from depmesh.discovery.expressions.entities import EvaluationContext
from depmesh.discovery.matchers import CaptureName
from depmesh.domain.entities import ArtifactId

if TYPE_CHECKING:
    from depmesh.discovery.expressions import DependencyExpression


class UnionExpression(BaseEntity):
    type: Literal["union"]
    items: tuple[DependencyExpression, ...] = pydantic.Field(min_length=1)

    def variables(self) -> set[CaptureName]:
        return set().union(*(item.variables() for item in self.items))

    def evaluate(self, context: EvaluationContext) -> list[ArtifactId]:
        dependencies: set[ArtifactId] = set()

        for item in self.items:
            dependencies.update(item.evaluate(context))

        return sorted(dependencies)
