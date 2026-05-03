from __future__ import annotations

import re

from depmesh.discovery.predicates.base import ArtifactPredicateBase
from depmesh.discovery.predicates.entities import RegexPattern, RegexPredicateConfig
from depmesh.domain.entities import ArtifactId, ProjectRootPath


class RegexPredicate(ArtifactPredicateBase):
    __slots__ = ("config",)

    def __init__(self, config: RegexPredicateConfig) -> None:
        self.config = config

    def match(
        self,
        artifact: ArtifactId,
        root: ProjectRootPath,
        captures: dict[str, str] | None = None,
    ) -> dict[str, str] | None:
        pattern = self.config.pattern.substitute(captures or {})
        match = re.compile(pattern).match(artifact)
        return match.groupdict() if match else None


__all__ = ["RegexPattern", "RegexPredicate", "RegexPredicateConfig"]
