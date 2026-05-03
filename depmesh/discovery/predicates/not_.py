from __future__ import annotations

from depmesh.discovery.predicates.base import ArtifactPredicateBase
from depmesh.discovery.predicates.entities import NotPredicateConfig
from depmesh.domain.entities import ArtifactId, ProjectRootPath


class NotPredicate(ArtifactPredicateBase):
    __slots__ = ("config", "item")

    def __init__(self, config: NotPredicateConfig, item: ArtifactPredicateBase) -> None:
        self.config = config
        self.item = item

    def match(
        self,
        artifact: ArtifactId,
        root: ProjectRootPath,
        captures: dict[str, str] | None = None,
    ) -> dict[str, str] | None:
        return {} if self.item.match(artifact, root, captures) is None else None


__all__ = ["NotPredicate", "NotPredicateConfig"]
