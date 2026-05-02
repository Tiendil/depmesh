from __future__ import annotations

from pathlib import Path
from typing import Literal, NewType

import pydantic

from depmesh.core.entities import BaseEntity
from depmesh.discovery.matchers.entities import CaptureName
from depmesh.discovery.paths import normalize_path
from depmesh.domain.entities import ArtifactId

PathsMatcherValue = NewType("PathsMatcherValue", str)


class PathsMatcher(BaseEntity):
    type: Literal["paths"]
    paths: tuple[PathsMatcherValue, ...] = pydantic.Field(min_length=1)

    def captures(self) -> set[CaptureName]:
        return set()

    def match(self, artifact: ArtifactId, root: Path) -> dict[str, str] | None:
        for path in self.paths:
            if artifact == normalize_path(path, root):
                return {}
        return None
