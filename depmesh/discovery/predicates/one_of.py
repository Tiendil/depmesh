from __future__ import annotations

from typing import Literal, NewType

import pydantic

from depmesh.discovery.artifacts import CaptureName, TemplateText
from depmesh.discovery.predicates.base import ArtifactPredicateBase
from depmesh.discovery.paths import normalize_path
from depmesh.domain.entities import ArtifactId, ProjectRootPath

OneOfPredicateValue = NewType("OneOfPredicateValue", str)


class OneOfPredicate(ArtifactPredicateBase):
    type: Literal["one_of"]
    artifacts: tuple[TemplateText, ...] = pydantic.Field(min_length=1)

    def variables(self) -> set[CaptureName]:
        return set().union(*(artifact.variables for artifact in self.artifacts))

    def match(
        self,
        artifact: ArtifactId,
        root: ProjectRootPath,
        captures: dict[str, str] | None = None,
    ) -> dict[str, str] | None:
        captures = captures or {}

        for expected in self.artifacts:
            if artifact == normalize_path(expected.substitute(captures), root):
                return {}

        return None
