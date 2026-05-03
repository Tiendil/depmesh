from __future__ import annotations

from typing import TYPE_CHECKING, Literal

import pydantic

from depmesh.discovery.artifacts import CaptureName
from depmesh.discovery.predicates.base import ArtifactPredicateBase
from depmesh.domain.entities import ArtifactId, ProjectRootPath

if TYPE_CHECKING:
    from depmesh.discovery.predicates import ArtifactPredicate


class AnyPredicate(ArtifactPredicateBase):
    type: Literal["any"]
    items: tuple[ArtifactPredicate, ...] = pydantic.Field(min_length=1)

    def variables(self) -> set[CaptureName]:
        return set().union(*(item.variables() for item in self.items))

    def captures(self) -> set[CaptureName]:
        captures = [item.captures() for item in self.items]
        return set.intersection(*captures) if captures else set()

    def match(
        self,
        artifact: ArtifactId,
        root: ProjectRootPath,
        captures: dict[str, str] | None = None,
    ) -> dict[str, str] | None:
        for item in self.items:
            result = item.match(artifact, root, captures)
            if result is not None:
                return result

        return None
