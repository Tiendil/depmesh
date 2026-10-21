from __future__ import annotations

from llm_tool_cli.paths import ProjectRootPath, normalize_path

from depmesh.discovery.predicates.base import ArtifactPredicateBase
from depmesh.discovery.predicates.entities import OneOfPredicateConfig, OneOfPredicateValue
from depmesh.domain.entities import ArtifactId


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
            if artifact == ArtifactId(normalize_path(expected.substitute(captures), root).unwrap()):
                return {}

        return None


__all__ = ["OneOfPredicate", "OneOfPredicateConfig", "OneOfPredicateValue"]
