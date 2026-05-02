from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Literal

import pydantic

from depmesh.core.entities import BaseEntity
from depmesh.discovery.matchers.entities import CaptureName
from depmesh.domain.entities import ArtifactId

if TYPE_CHECKING:
    from depmesh.discovery.matchers import ArtifactMatcher


class AllMatcher(BaseEntity):
    type: Literal["all"]
    items: tuple[ArtifactMatcher, ...] = pydantic.Field(min_length=1)

    def captures(self) -> set[CaptureName]:
        return set().union(*(item.captures() for item in self.items))

    def match(self, artifact: ArtifactId, root: Path) -> dict[str, str] | None:
        result: dict[str, str] = {}

        for item in self.items:
            captures = item.match(artifact, root)
            if captures is None:
                return None

            for name, value in captures.items():
                if name in result and result[name] != value:
                    return None
                result[name] = value

        return result
