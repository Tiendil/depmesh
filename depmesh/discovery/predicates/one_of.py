from __future__ import annotations

from depmesh.discovery.predicates.base import ArtifactPredicateBase
from depmesh.discovery.predicates.entities import OneOfPredicateConfig, OneOfPredicateValue
from depmesh.discovery.paths import normalize_path
from depmesh.domain.entities import ArtifactId, ProjectRootPath


class OneOfPredicate(ArtifactPredicateBase):
    __slots__ = ("config",)

    def __init__(self, config: OneOfPredicateConfig) -> None:
        self.config = config

    def match(
        self,
        artifact: ArtifactId,
        root: ProjectRootPath,
        captures: dict[str, str] | None = None,
    ) -> dict[str, str] | None:
        captures = captures or {}

        for expected in self.config.artifacts:
            if artifact == normalize_path(expected.substitute(captures), root):
                return {}

        return None


__all__ = ["OneOfPredicate", "OneOfPredicateConfig", "OneOfPredicateValue"]
