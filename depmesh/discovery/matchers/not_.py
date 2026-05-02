from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Literal

from depmesh.core.entities import BaseEntity
from depmesh.discovery.matchers.entities import CaptureName
from depmesh.domain.entities import ArtifactId

if TYPE_CHECKING:
    from depmesh.discovery.matchers import ArtifactMatcher


class NotMatcher(BaseEntity):
    type: Literal["not"]
    item: ArtifactMatcher

    def captures(self) -> set[CaptureName]:
        return set()

    def match(self, artifact: ArtifactId, root: Path) -> dict[str, str] | None:
        return {} if self.item.match(artifact, root) is None else None
