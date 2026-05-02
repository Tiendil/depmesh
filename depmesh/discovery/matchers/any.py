from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Literal

import pydantic

from depmesh.core.entities import BaseEntity
from depmesh.discovery.matchers.entities import CaptureName
from depmesh.domain.entities import ArtifactId

if TYPE_CHECKING:
    from depmesh.discovery.matchers import ArtifactMatcher


class AnyMatcher(BaseEntity):
    type: Literal["any"]
    items: tuple[ArtifactMatcher, ...] = pydantic.Field(min_length=1)

    def captures(self) -> set[CaptureName]:
        captures = [item.captures() for item in self.items]
        return set.intersection(*captures) if captures else set()

    def match(self, artifact: ArtifactId, root: Path) -> dict[str, str] | None:
        for item in self.items:
            captures = item.match(artifact, root)
            if captures is not None:
                return captures

        return None
