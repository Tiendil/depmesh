from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from depmesh.discovery.artifacts import CaptureName
from depmesh.discovery.predicates.base import ArtifactPredicateBase
from depmesh.domain.entities import ArtifactId, ProjectRootPath

if TYPE_CHECKING:
    from depmesh.discovery.predicates import ArtifactPredicate


class NotPredicate(ArtifactPredicateBase):
    type: Literal["not"]
    item: ArtifactPredicate

    def variables(self) -> set[CaptureName]:
        return self.item.variables()

    def match(
        self,
        artifact: ArtifactId,
        root: ProjectRootPath,
        captures: dict[str, str] | None = None,
    ) -> dict[str, str] | None:
        return {} if self.item.match(artifact, root, captures) is None else None
