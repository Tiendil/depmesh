from __future__ import annotations

from depmesh.discovery.predicates.base import ArtifactPredicateBase
from depmesh.discovery.predicates.entities import AllPredicateConfig
from depmesh.domain.entities import ArtifactId, ProjectRootPath


class AllPredicate(ArtifactPredicateBase):
    __slots__ = ("config", "items")

    def __init__(self, config: AllPredicateConfig, items: tuple[ArtifactPredicateBase, ...]) -> None:
        self.config = config
        self.items = items

    def match(
        self,
        artifact: ArtifactId,
        root: ProjectRootPath,
        captures: dict[str, str] | None = None,
    ) -> dict[str, str] | None:
        result: dict[str, str] = {}

        for item in self.items:
            item_captures = item.match(artifact, root, captures)
            if item_captures is None:
                return None

            for name, value in item_captures.items():
                if name in result and result[name] != value:
                    return None
                result[name] = value

        return result


__all__ = ["AllPredicate", "AllPredicateConfig"]
