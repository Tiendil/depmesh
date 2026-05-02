from __future__ import annotations

from pathlib import Path
from typing import Literal, NewType

import pydantic

from depmesh.core.entities import BaseEntity
from depmesh.discovery.artifacts import CaptureName, TemplateText
from depmesh.discovery.paths import normalize_path
from depmesh.domain.entities import ArtifactId

OneOfPredicateValue = NewType("OneOfPredicateValue", str)


class OneOfPredicate(BaseEntity):
    type: Literal["one_of"]
    artifacts: tuple[TemplateText, ...] = pydantic.Field(min_length=1)

    def variables(self) -> set[CaptureName]:
        return set().union(*(artifact.variables for artifact in self.artifacts))

    def captures(self) -> set[CaptureName]:
        return set()

    def match(self, artifact: ArtifactId, root: Path, captures: dict[str, str] | None = None) -> dict[str, str] | None:
        captures = captures or {}

        for expected in self.artifacts:
            if artifact == normalize_path(expected.substitute(captures), root):
                return {}

        return None
