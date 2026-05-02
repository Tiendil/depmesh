from __future__ import annotations

from typing import TYPE_CHECKING, Literal

import pydantic

from depmesh.core.entities import BaseEntity
from depmesh.discovery.expressions.entities import EvaluationContext
from depmesh.discovery.matchers import CaptureName
from depmesh.domain.entities import ArtifactId

if TYPE_CHECKING:
    from depmesh.discovery.expressions import DependencyExpression


class IntersectionExpression(BaseEntity):
    type: Literal["intersection"]
    items: tuple[DependencyExpression, ...] = pydantic.Field(min_length=1)

    def variables(self) -> set[CaptureName]:
        return set().union(*(item.variables() for item in self.items))

    def evaluate(self, context: EvaluationContext) -> list[ArtifactId]:
        dependency_sets = [set(item.evaluate(context)) for item in self.items]
        return sorted(set.intersection(*dependency_sets)) if dependency_sets else []
