from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Literal

import pydantic

from depmesh.core.entities import BaseEntity
from depmesh.discovery.artifacts import CaptureName
from depmesh.domain.entities import ArtifactId

if TYPE_CHECKING:
    from depmesh.discovery.predicates import ArtifactPredicate


class AllPredicate(BaseEntity):
    type: Literal["all"]
    items: tuple[ArtifactPredicate, ...] = pydantic.Field(min_length=1)

    def variables(self) -> set[CaptureName]:
        return set().union(*(item.variables() for item in self.items))

    def captures(self) -> set[CaptureName]:
        return set().union(*(item.captures() for item in self.items))

    def match(self, artifact: ArtifactId, root: Path, captures: dict[str, str] | None = None) -> dict[str, str] | None:
        result: dict[str, str] = {}

        for item in self.items:
            item_captures = item.match(artifact, root, captures)
            if item_captures is None:
                return None

            for name, value in item_captures.items():
                if name in result and result[name] != value:
                    return None
                result[name] = value

        return result
