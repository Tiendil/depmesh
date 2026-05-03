from __future__ import annotations

import re
from typing import Literal, NewType

from depmesh.discovery.artifacts import CaptureName, TemplateText
from depmesh.discovery.predicates.base import ArtifactPredicateBase
from depmesh.domain.entities import ArtifactId, ProjectRootPath

RegexPattern = NewType("RegexPattern", str)


class RegexPredicate(ArtifactPredicateBase):
    type: Literal["regex"]
    pattern: TemplateText

    def variables(self) -> set[CaptureName]:
        return set(self.pattern.variables)

    def captures(self) -> set[CaptureName]:
        try:
            return {CaptureName(name) for name in re.compile(self.pattern.value).groupindex}
        except re.error as error:
            raise ValueError(f"invalid regex predicate: {error}") from error

    def match(
        self,
        artifact: ArtifactId,
        root: ProjectRootPath,
        captures: dict[str, str] | None = None,
    ) -> dict[str, str] | None:
        pattern = self.pattern.substitute(captures or {})
        match = re.compile(pattern).match(artifact)
        return match.groupdict() if match else None
