from __future__ import annotations

from pathlib import Path
from typing import Literal, NewType

from depmesh.core.entities import BaseEntity
from depmesh.discovery.matchers.entities import CaptureName
from depmesh.discovery.paths import normalize_path
from depmesh.domain.entities import ArtifactId

PathMatcherValue = NewType("PathMatcherValue", str)


class PathMatcher(BaseEntity):
    type: Literal["path"]
    path: PathMatcherValue

    def captures(self) -> set[CaptureName]:
        return set()

    def match(self, artifact: ArtifactId, root: Path) -> dict[str, str] | None:
        pattern = normalize_path(self.path, root)
        return {} if artifact == pattern else None
