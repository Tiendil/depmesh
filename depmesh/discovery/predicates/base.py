from __future__ import annotations

from depmesh.core.entities import BaseEntity
from depmesh.discovery.artifacts import CaptureName
from depmesh.domain.entities import ArtifactId, ProjectRootPath


class ArtifactPredicateBase(BaseEntity):
    def variables(self) -> set[CaptureName]:
        return set()

    def captures(self) -> set[CaptureName]:
        return set()

    def match(
        self,
        artifact: ArtifactId,
        root: ProjectRootPath,
        captures: dict[str, str] | None = None,
    ) -> dict[str, str] | None:
        raise NotImplementedError
