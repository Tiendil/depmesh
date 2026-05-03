from __future__ import annotations

from depmesh.discovery.predicates.base import ArtifactPredicateBase
from depmesh.discovery.predicates.entities import AnyPredicateConfig
from depmesh.domain.entities import ArtifactId, ProjectRootPath


class AnyPredicate(ArtifactPredicateBase):
    __slots__ = ("config", "items")

    def __init__(self, config: AnyPredicateConfig, items: tuple[ArtifactPredicateBase, ...]) -> None:
        self.config = config
        self.items = items

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


__all__ = ["AnyPredicate", "AnyPredicateConfig"]
